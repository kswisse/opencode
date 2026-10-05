import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from src.services.auth import create_access_token


def get_auth_header():
    token = create_access_token(str(uuid4()), str(uuid4()), "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_create_agent(client):
    with patch("src.api.v1.agents.AgentFactory") as MockFactory:
        from src.models.agent import Agent
        mock_factory = AsyncMock()
        MockFactory.return_value = mock_factory
        mock_factory.create_agent = AsyncMock(return_value=Agent(
            id=uuid4(), company_id=uuid4(), name="Test Writer",
            agent_type="writer", status="idle", model="gpt-4o-mini",
            performance_score=0.0, total_tasks=0, successful_tasks=0,
            created_at=datetime.now(timezone.utc),
        ))
        response = await client.post(
            "/api/v1/agents",
            json={"name": "Test Writer", "agent_type": "writer"},
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Writer"


@pytest.mark.asyncio
async def test_list_agents(client):
    with patch("src.api.v1.agents.AgentFactory") as MockFactory:
        mock_factory = AsyncMock()
        MockFactory.return_value = mock_factory
        mock_factory.list_agents = AsyncMock(return_value=[])
        response = await client.get(
            "/api/v1/agents",
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_memory(client):
    with patch("src.api.v1.memory.MemoryService") as MockService:
        mock_service = AsyncMock()
        MockService.return_value = mock_service
        mock_service.search_episodic = AsyncMock(return_value=[])
        mock_service.search_semantic = AsyncMock(return_value=[])
        response = await client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 5},
            headers=get_auth_header(),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0
