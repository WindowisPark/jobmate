async def schedule_routine(
    title: str,
    description: str | None = None,
    recurrence: str = "daily",
    time: str = "09:00",
) -> dict:
    """취준 루틴을 등록합니다."""
    # TODO: Google Calendar API 연동
    return {
        "status": "mock",
        "event": {
            "title": title,
            "description": description,
            "recurrence": recurrence,
            "time": time,
        },
    }
