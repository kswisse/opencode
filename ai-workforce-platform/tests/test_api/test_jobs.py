import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.auth import create_access_token


def get_auth_header():
    """Create a valid auth header."""
    token = create_access_token(str(uuid.uuid4()), str(uuid.uuid4()), "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_background_job_service():
    """Create a mock BackgroundJobService."""
    service = AsyncMock()
    return service


class TestJobsAPI:
    """Tests for Jobs API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_job(self, mock_background_job_service):
        """Test getting a job by ID."""
        job_id = uuid.uuid4()
        
        mock_job = MagicMock()
        mock_job.id = job_id
        mock_job.goal_id = uuid.uuid4()
        mock_job.job_type = "execute_task"
        mock_job.status = "completed"
        mock_job.payload = {"task_id": str(uuid.uuid4())}
        mock_job.result = {"output": "test"}
        mock_job.error_message = None
        mock_job.retry_count = 0
        mock_job.max_retries = 3
        mock_job.worker_id = "worker-123"
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.started_at = datetime.now(timezone.utc)
        mock_job.completed_at = datetime.now(timezone.utc)
        
        mock_background_job_service.get_job.return_value = mock_job
        
        with patch("src.api.v1.jobs.BackgroundJobService", return_value=mock_background_job_service):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/jobs/{job_id}",
                    headers=get_auth_header(),
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job_id)
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, mock_background_job_service):
        """Test getting a job that doesn't exist."""
        job_id = uuid.uuid4()
        
        mock_background_job_service.get_job.return_value = None
        
        with patch("src.api.v1.jobs.BackgroundJobService", return_value=mock_background_job_service):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/jobs/{job_id}",
                    headers=get_auth_header(),
                )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_project_jobs(self, mock_background_job_service):
        """Test getting jobs for a project."""
        project_id = uuid.uuid4()
        
        mock_jobs = [MagicMock() for _ in range(3)]
        for job in mock_jobs:
            job.id = uuid.uuid4()
            job.goal_id = project_id
            job.job_type = "execute_task"
            job.status = "completed"
            job.created_at = datetime.now(timezone.utc)
            job.completed_at = datetime.now(timezone.utc)
        
        mock_background_job_service.get_jobs_by_project.return_value = mock_jobs
        
        with patch("src.api.v1.jobs.BackgroundJobService", return_value=mock_background_job_service):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/jobs/project/{project_id}",
                    headers=get_auth_header(),
                )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 3
    
    @pytest.mark.asyncio
    async def test_retry_job(self, mock_background_job_service):
        """Test retrying a failed job."""
        job_id = uuid.uuid4()
        
        mock_job = MagicMock()
        mock_job.id = job_id
        mock_job.status = "queued"
        
        mock_background_job_service.retry_job.return_value = mock_job
        
        with patch("src.api.v1.jobs.BackgroundJobService", return_value=mock_background_job_service):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/jobs/{job_id}/retry",
                    headers=get_auth_header(),
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, mock_background_job_service):
        """Test cancelling a queued job."""
        job_id = uuid.uuid4()
        
        mock_job = MagicMock()
        mock_job.id = job_id
        mock_job.status = "cancelled"
        
        mock_background_job_service.cancel_job.return_value = mock_job
        
        with patch("src.api.v1.jobs.BackgroundJobService", return_value=mock_background_job_service):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/jobs/{job_id}/cancel",
                    headers=get_auth_header(),
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
