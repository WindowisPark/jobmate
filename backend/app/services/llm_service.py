import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from openai import AsyncOpenAI, APITimeoutError, APIConnectionError

from app.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 1

# 에이전트 ID → 표시 이름 매핑
_AGENT_NAMES: dict[str, str] = {
    "seo_yeon": "김서연",
    "jun_ho": "박준호",
    "ha_eun": "이하은",
    "min_su": "정민수",
}

_client: AsyncOpenAI | None = None


def _format_history(history: list[dict]) -> list[dict]:
    """DB 히스토리를 OpenAI 메시지 형식으로 변환한다."""
    formatted: list[dict] = []
    for entry in history:
        if entry["role"] == "user":
            formatted.append({"role": "user", "content": entry["content"]})
        else:
            agent_id = entry.get("agent_id", "")
            name = _AGENT_NAMES.get(agent_id, agent_id)
            formatted.append({
                "role": "assistant",
                "content": f"[{name}] {entry['content']}",
            })
    return formatted


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
        )
    return _client


async def generate_response(
    system_prompt: str,
    user_message: str,
    history: list[dict] | None = None,
) -> str:
    """GPT-4o mini로 텍스트 응답을 생성한다 (Tool 없음)."""
    client = get_openai_client()
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(_format_history(history))

    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.8,
            max_tokens=500,
        )
        return response.choices[0].message.content or ""
    except (APITimeoutError, APIConnectionError) as e:
        logger.error(f"LLM API error: {e}")
        raise RuntimeError("AI 응답 생성에 실패했습니다. 잠시 후 다시 시도해주세요.") from e
    except Exception as e:
        logger.error(f"LLM unexpected error: {e}", exc_info=True)
        raise RuntimeError("AI 응답 생성 중 오류가 발생했습니다.") from e


async def generate_response_with_tools(
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    tool_executor: Callable[[str, dict], Awaitable[dict]],
    history: list[dict] | None = None,
) -> tuple[str, list[dict] | None]:
    """GPT-4o mini로 Tool Calling을 포함한 응답을 생성한다."""
    client = get_openai_client()
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(_format_history(history))

    messages.append({"role": "user", "content": user_message})

    try:
        # 1차 호출: GPT가 tool 호출 여부 판단
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=0.8,
            max_tokens=500,
        )
    except (APITimeoutError, APIConnectionError) as e:
        logger.error(f"LLM API error (1st call): {e}")
        raise RuntimeError("AI 응답 생성에 실패했습니다.") from e

    assistant_msg = response.choices[0].message
    tool_calls_raw = assistant_msg.tool_calls

    # Tool 호출이 없으면 바로 반환
    if not tool_calls_raw:
        return assistant_msg.content or "", None

    # Tool 호출 실행
    tool_records: list[dict] = []
    messages.append(assistant_msg.model_dump())

    for tc in tool_calls_raw:
        fn_name = tc.function.name
        try:
            fn_args = json.loads(tc.function.arguments)
        except json.JSONDecodeError:
            fn_args = {}

        logger.info(f"Tool call: {fn_name}({fn_args})")

        try:
            result = await asyncio.wait_for(
                tool_executor(fn_name, fn_args),
                timeout=15,
            )
        except asyncio.TimeoutError:
            logger.error(f"Tool execution timed out: {fn_name}")
            result = {"error": f"도구 실행 시간이 초과되었습니다: {fn_name}"}
        except Exception as e:
            logger.error(f"Tool execution failed: {fn_name} — {e}")
            result = {"error": f"도구 실행 중 오류가 발생했습니다: {str(e)}"}

        tool_records.append({
            "name": fn_name,
            "args": fn_args,
            "result": result,
        })

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        })

    try:
        # 2차 호출: Tool 결과를 반영한 최종 응답
        final_response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.8,
            max_tokens=800,
        )
    except (APITimeoutError, APIConnectionError) as e:
        logger.error(f"LLM API error (2nd call): {e}")
        raise RuntimeError("AI 응답 생성에 실패했습니다.") from e

    final_content = final_response.choices[0].message.content or ""
    logger.info(f"Tool calling complete: {[r['name'] for r in tool_records]}")

    return final_content, tool_records
