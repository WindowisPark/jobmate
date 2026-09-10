"""도구 실행기 — 네 노드가 함께 쓴다.

노드마다 사본을 두면 DB 세션이 필요한 도구를 붙일 때 한 곳을 빠뜨린다.
실제로 그랬다. 탐색이 노드만 user_id 를 주입하고 세션은 빠뜨려
save_job_preferences 는 늘 "DB 세션이 필요합니다" 를 돌려줬고,
search_jobs 는 캐시를 저장하지 못해 매번 스크래핑했다.
주입 지점을 여기 하나로 모아 같은 실수가 반복되지 않게 한다.
"""

from collections.abc import Awaitable, Callable

from app.dependencies import async_session
from app.tools import ALL_TOOLS

# DB 세션과 user_id 를 서버가 채워주는 도구. LLM 이 정할 값이 아니다.
DB_AWARE_TOOLS: frozenset[str] = frozenset(
    {"search_jobs", "save_job_preferences", "get_my_applications", "update_application_status"}
)

# 서버가 채우는 인자 — 모델이 넣어 보내도 무시한다(중복 인자 TypeError 방지)
_SERVER_ARGS = ("db", "user_id")

ToolExecutor = Callable[[str, dict], Awaitable[dict]]


def make_tool_executor(user_id: str) -> ToolExecutor:
    """이 대화의 도구 실행기를 만든다. DB 세션은 도구 호출 단위로 열고 닫는다."""

    async def execute_tool(name: str, args: dict) -> dict:
        fn = ALL_TOOLS.get(name)
        if fn is None:
            return {"error": f"알 수 없는 도구: {name}"}

        if name not in DB_AWARE_TOOLS:
            return await fn(**args)

        if not user_id:
            return {"error": "로그인이 필요한 도구예요"}

        safe_args = {k: v for k, v in args.items() if k not in _SERVER_ARGS}
        async with async_session() as db:
            result = await fn(**safe_args, user_id=user_id, db=db)
            # 도구는 flush 만 한다 — 커밋은 여기서. 없으면 공고 캐시가 저장되지 않는다.
            await db.commit()
            return result

    return execute_tool
