import pytest


@pytest.fixture
def sample_user_message() -> dict:
    return {
        "type": "user_message",
        "content": "오늘 면접 망한 것 같아...",
    }
