import pytest
import uuid
from unittest.mock import AsyncMock, patch

from src.services.ceo_agent import CEODecomposeAgent


MOCK_LLM_RESPONSE = {
    "projects": [
        {
            "name": "Affiliate Marketing Setup",
            "tasks": [
                {"name": "Research profitable niches", "description": "Find top 5 niches", "priority": 1, "depends_on": [], "wave": 1},
                {"name": "Join affiliate programs", "description": "Sign up for programs", "priority": 2, "depends_on": ["Research profitable niches"], "wave": 2},
                {"name": "Create content plan", "description": "Plan 30 days of content", "priority": 2, "depends_on": ["Research profitable niches"], "wave": 2},
            ],
        }
    ]
}


@pytest.mark.asyncio
async def test_ceo_decompose(mock_db):
    with patch("src.services.ceo_agent.llm_client") as mock_llm:
        mock_llm.json = AsyncMock(return_value=MOCK_LLM_RESPONSE)

        agent = CEODecomposeAgent(mock_db)
        project = await agent.decompose(
            company_id=uuid.uuid4(),
            goal_text="Earn $10,000/month with affiliate marketing",
        )

        assert project.name == "Affiliate Marketing Setup"
        assert project.status == "active"
        mock_db.add.assert_called()
