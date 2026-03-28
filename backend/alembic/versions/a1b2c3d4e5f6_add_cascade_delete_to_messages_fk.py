"""add cascade delete to messages FK

Revision ID: a1b2c3d4e5f6
Revises: fbcc2b586f54
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "fbcc2b586f54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # messages.conversation_id FK에 ON DELETE CASCADE 추가
    op.drop_constraint(
        "messages_conversation_id_fkey", "messages", type_="foreignkey"
    )
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # user_emotion_logs.conversation_id FK에도 ON DELETE CASCADE 추가
    op.drop_constraint(
        "user_emotion_logs_conversation_id_fkey",
        "user_emotion_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_emotion_logs_conversation_id_fkey",
        "user_emotion_logs",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # user_emotion_logs FK 원복
    op.drop_constraint(
        "user_emotion_logs_conversation_id_fkey",
        "user_emotion_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_emotion_logs_conversation_id_fkey",
        "user_emotion_logs",
        "conversations",
        ["conversation_id"],
        ["id"],
    )

    # messages FK 원복
    op.drop_constraint(
        "messages_conversation_id_fkey", "messages", type_="foreignkey"
    )
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
    )
