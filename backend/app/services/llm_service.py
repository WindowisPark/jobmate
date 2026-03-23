import json
import logging
from collections.abc import Awaitable, Callable

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_response(system_prompt: str, user_message: str) -> str:
    """GPT-4o mini로 텍스트 응답을 생성한다 (Tool 없음)."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


async def generate_response_with_tools(
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    tool_executor: Callable[[str, dict], Awaitable[dict]],
) -> tuple[str, list[dict] | None]:
    """GPT-4o mini로 Tool Calling을 포함한 응답을 생성한다.

    Returns:
        (최종 텍스트 응답, Tool 호출 기록 리스트 or None)
    """
    client = get_openai_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # 1차 호출: GPT가 tool 호출 여부 판단
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
        temperature=0.8,
        max_tokens=500,
    )

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

        # Tool 실행
        try:
            result = await tool_executor(fn_name, fn_args)
        except Exception as e:
            logger.error(f"Tool execution failed: {fn_name} — {e}")
            result = {"error": f"도구 실행 중 오류가 발생했습니다: {str(e)}"}

        tool_records.append({
            "name": fn_name,
            "args": fn_args,
            "result": result,
        })

        # Tool 결과를 대화에 추가
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        })

    # 2차 호출: Tool 결과를 반영한 최종 응답
    final_response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.8,
        max_tokens=800,
    )

    final_content = final_response.choices[0].message.content or ""
    logger.info(f"Tool calling complete: {[r['name'] for r in tool_records]}")

    return final_content, tool_records
