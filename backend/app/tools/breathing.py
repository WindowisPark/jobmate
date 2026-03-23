async def breathing_exercise(
    technique: str = "4-7-8",
    duration_minutes: int = 3,
) -> dict:
    """호흡 운동 가이드를 생성합니다."""
    techniques = {
        "4-7-8": {
            "name": "4-7-8 호흡법",
            "steps": [
                {"action": "숨 들이쉬기", "seconds": 4},
                {"action": "숨 참기", "seconds": 7},
                {"action": "숨 내쉬기", "seconds": 8},
            ],
            "description": "불안을 줄이고 마음을 안정시키는 호흡법이에요.",
        },
        "box": {
            "name": "박스 호흡법",
            "steps": [
                {"action": "숨 들이쉬기", "seconds": 4},
                {"action": "숨 참기", "seconds": 4},
                {"action": "숨 내쉬기", "seconds": 4},
                {"action": "숨 참기", "seconds": 4},
            ],
            "description": "집중력을 높이고 스트레스를 줄이는 호흡법이에요.",
        },
    }

    selected = techniques.get(technique, techniques["4-7-8"])
    cycles = (duration_minutes * 60) // sum(s["seconds"] for s in selected["steps"])

    return {
        **selected,
        "cycles": cycles,
        "total_minutes": duration_minutes,
    }
