#!/bin/sh
set -e

echo "==> Running Alembic migrations..."
python -m alembic upgrade head

echo "==> Seeding agents table..."
python -c "
import asyncio
from app.dependencies import async_session
from app.models.agent_state import Agent
from sqlalchemy import select

AGENTS = [
    {'id': 'seo_yeon', 'name': '김서연', 'role': 'Career Coach', 'personality': '따뜻하지만 직설적인 커리어 코치', 'avatar_url': '/assets/agents/seo-yeon.svg'},
    {'id': 'jun_ho', 'name': '박준호', 'role': 'Job Researcher', 'personality': '데이터 중심의 꼼꼼한 리서처', 'avatar_url': '/assets/agents/jun-ho.svg'},
    {'id': 'ha_eun', 'name': '이하은', 'role': 'Mental Care', 'personality': '공감 능력이 뛰어난 멘탈 케어 전문가', 'avatar_url': '/assets/agents/ha-eun.svg'},
    {'id': 'min_su', 'name': '정민수', 'role': 'Industry Mentor', 'personality': '현직자 형/누나 느낌의 멘토', 'avatar_url': '/assets/agents/min-su.svg'},
]

async def seed():
    async with async_session() as db:
        for a in AGENTS:
            result = await db.execute(select(Agent).where(Agent.id == a['id']))
            if result.scalar_one_or_none() is None:
                db.add(Agent(**a))
        await db.commit()
        print('  Agents seeded.')

asyncio.run(seed())
"

echo "==> Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
