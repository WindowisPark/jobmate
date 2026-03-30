"""감정 이력 추적 및 패턴 분석 서비스."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_state import UserEmotionLog

# 부정적 감정 목록
NEGATIVE_EMOTIONS = {"anxious", "depressed", "angry", "frustrated"}

EMOTION_LABELS_KR = {
    "neutral": "보통",
    "anxious": "불안",
    "depressed": "우울",
    "angry": "화남",
    "hopeful": "희망적",
    "frustrated": "답답",
}


async def save_emotion_log(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    emotion: str,
    intensity: int,
    context: str | None = None,
) -> None:
    """감정 로그를 DB에 저장한다."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        conv_uuid = None

    log = UserEmotionLog(
        user_id=user_uuid,
        conversation_id=conv_uuid,
        emotion=emotion,
        intensity=intensity,
        context=context,
    )
    db.add(log)


async def get_emotion_history(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
) -> list[dict]:
    """최근 N일간 감정 이력을 조회한다."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return []

    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(UserEmotionLog)
        .where(
            UserEmotionLog.user_id == user_uuid,
            UserEmotionLog.created_at >= since,
        )
        .order_by(UserEmotionLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "emotion": log.emotion,
            "intensity": log.intensity,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


def detect_emotion_patterns(history: list[dict]) -> list[str]:
    """감정 이력에서 패턴을 감지한다."""
    if not history:
        return []

    patterns = []

    # 최근 3회 연속 동일 부정 감정
    if len(history) >= 3:
        recent_3 = [h["emotion"] for h in history[:3]]
        if len(set(recent_3)) == 1 and recent_3[0] in NEGATIVE_EMOTIONS:
            label = EMOTION_LABELS_KR.get(recent_3[0], recent_3[0])
            patterns.append(f"최근 3회 연속 '{label}' 상태")

    # 평균 강도 분석
    if len(history) >= 3:
        avg_intensity = sum(h["intensity"] for h in history[:5]) / min(len(history), 5)
        if avg_intensity >= 4.0:
            patterns.append("최근 감정 강도가 매우 높은 상태 (평균 4 이상)")
        elif avg_intensity <= 2.0 and history[0]["emotion"] not in NEGATIVE_EMOTIONS:
            patterns.append("전반적으로 안정적인 상태")

    # 개선 추세 감지
    if len(history) >= 4:
        recent_avg = sum(h["intensity"] for h in history[:2]) / 2
        older_avg = sum(h["intensity"] for h in history[2:4]) / 2
        if older_avg - recent_avg >= 1.5:
            patterns.append("감정 상태가 개선되는 추세")
        elif recent_avg - older_avg >= 1.5:
            patterns.append("감정 상태가 악화되는 추세")

    # 부정 감정 비율
    if len(history) >= 5:
        negative_count = sum(1 for h in history[:7] if h["emotion"] in NEGATIVE_EMOTIONS)
        if negative_count >= 5:
            patterns.append("최근 대화에서 부정적 감정이 빈번")

    return patterns


async def get_emotion_summary(db: AsyncSession, user_id: str) -> str:
    """하은이의 시스템 프롬프트에 주입할 감정 이력 요약을 생성한다."""
    history = await get_emotion_history(db, user_id, days=7)

    if not history:
        return ""

    patterns = detect_emotion_patterns(history)
    if not patterns:
        return ""

    summary_parts = ["[사용자 감정 이력 분석]"]
    for p in patterns:
        summary_parts.append(f"- {p}")

    # 최근 감정 흐름
    recent = history[:5]
    flow = " → ".join(
        f"{EMOTION_LABELS_KR.get(h['emotion'], h['emotion'])}({h['intensity']})"
        for h in reversed(recent)
    )
    summary_parts.append(f"최근 감정 흐름: {flow}")
    summary_parts.append("이 정보를 바탕으로 사용자의 감정 변화를 자연스럽게 언급해줘.")

    return "\n".join(summary_parts)
