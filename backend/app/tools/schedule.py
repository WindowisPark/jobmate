from datetime import datetime


async def schedule_routine(
    title: str,
    description: str | None = None,
    recurrence: str = "daily",
    time: str = "09:00",
) -> dict:
    """취준 루틴을 등록합니다 (현재 mock)."""
    recurrence_label = {
        "daily": "매일",
        "weekdays": "평일",
        "weekly": "매주",
    }.get(recurrence, recurrence)

    return {
        "status": "scheduled",
        "event": {
            "title": title,
            "description": description,
            "recurrence": recurrence,
            "time": time,
        },
        "created_at": datetime.now().isoformat(),
        "reminder": f"{recurrence_label} {time}에 '{title}' 알림을 보내줄게!",
    }
