from app.api.middleware.auth import create_access_token, create_refresh_token
from uuid import uuid4


def test_create_access_token():
    user_id = uuid4()
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0
