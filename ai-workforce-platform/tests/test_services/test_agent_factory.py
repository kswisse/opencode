import pytest
import uuid

from src.services.agent_factory import AgentFactory
from src.schemas.agent import AgentCreate


@pytest.mark.asyncio
async def test_create_agent(mock_db):
    factory = AgentFactory(mock_db)
    agent = await factory.create_agent(
        company_id=uuid.uuid4(),
        request=AgentCreate(name="Research Agent", agent_type="researcher"),
    )
    assert agent.name == "Research Agent"
    assert agent.agent_type == "researcher"
    assert agent.status == "idle"
    assert "research" in agent.system_prompt.lower()
