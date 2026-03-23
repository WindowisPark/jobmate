from app.agents.router import route_agents, INTENT_ROUTING


async def test_route_agents_default():
    state = {"intent": "general", "emotion": "neutral", "emotion_intensity": 2}
    result = await route_agents(state)
    assert "ha_eun" in result["active_agents"]


async def test_route_agents_high_anxiety_adds_ha_eun():
    state = {"intent": "job_search", "emotion": "anxious", "emotion_intensity": 4}
    result = await route_agents(state)
    assert result["active_agents"][0] == "ha_eun"


async def test_intent_routing_keys():
    expected = {"resume_interview", "job_search", "mental_care", "career_advice", "general"}
    assert set(INTENT_ROUTING.keys()) == expected
