import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.background_job import BackgroundJob
from src.services.background_job_service import BackgroundJobService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create a BackgroundJobService instance."""
    return BackgroundJobService(mock_db)


class TestBackgroundJobService:
    """Tests for BackgroundJobService."""
    
    @pytest.mark.asyncio
    async def test_get_job(self, service, mock_db):
        """Test getting a job by ID."""
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=BackgroundJob)
        mock_job.id = job_id
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result
        
        result = await service.get_job(job_id)
        
        assert result == mock_job
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, service, mock_db):
        """Test getting a job that doesn't exist."""
        job_id = uuid.uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await service.get_job(job_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_jobs_by_project(self, service, mock_db):
        """Test getting jobs for a project."""
        project_id = uuid.uuid4()
        mock_jobs = [MagicMock(spec=BackgroundJob) for _ in range(3)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_db.execute.return_value = mock_result
        
        result = await service.get_jobs_by_project(project_id)
        
        assert len(result) == 3
        assert result == mock_jobs
    
    @pytest.mark.asyncio
    async def test_get_job_stats(self, service, mock_db):
        """Test getting job statistics."""
        project_id = uuid.uuid4()
        
        # Mock count queries
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock avg query
        mock_avg_result = MagicMock()
        mock_avg_result.scalar.return_value = 30.0
        
        mock_db.execute.side_effect = [
            mock_count_result,  # queued
            mock_count_result,  # running
            mock_count_result,  # completed
            mock_count_result,  # failed
            mock_count_result,  # retrying
            mock_avg_result,    # avg duration
        ]
        
        result = await service.get_job_stats(project_id)
        
        assert "total_jobs" in result
        assert "by_status" in result
        assert "avg_duration_seconds" in result
    
    @pytest.mark.asyncio
    async def test_retry_job(self, service, mock_db):
        """Test retrying a failed job."""
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=BackgroundJob)
        mock_job.id = job_id
        mock_job.status = "failed"
        
        # Mock get_job
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result
        
        result = await service.retry_job(job_id)
        
        assert result.status == "queued"
        assert result.error_message is None
        assert result.started_at is None
        assert result.completed_at is None
        assert result.worker_id is None
    
    @pytest.mark.asyncio
    async def test_retry_job_invalid_status(self, service, mock_db):
        """Test retrying a job with invalid status."""
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=BackgroundJob)
        mock_job.id = job_id
        mock_job.status = "running"  # Invalid status for retry
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError) as exc_info:
            await service.retry_job(job_id)
        
        assert "Cannot retry job in status" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, service, mock_db):
        """Test cancelling a queued job."""
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=BackgroundJob)
        mock_job.id = job_id
        mock_job.status = "queued"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result
        
        result = await service.cancel_job(job_id)
        
        assert result.status == "cancelled"
        assert result.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_job_invalid_status(self, service, mock_db):
        """Test cancelling a job with invalid status."""
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=BackgroundJob)
        mock_job.id = job_id
        mock_job.status = "running"  # Invalid status for cancel
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError) as exc_info:
            await service.cancel_job(job_id)
        
        assert "Cannot cancel job in status" in str(exc_info.value)
