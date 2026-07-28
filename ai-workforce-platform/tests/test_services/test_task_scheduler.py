import pytest
import uuid
from unittest.mock import AsyncMock, patch

from src.services.task_scheduler import TaskScheduler
from src.models.task import Task


@pytest.mark.asyncio
async def test_compute_waves(mock_db):
    scheduler = TaskScheduler(mock_db)
    tasks = [
        Task(name="A", wave_number=1),
        Task(name="B", wave_number=1),
        Task(name="C", wave_number=2),
    ]
    waves = scheduler._compute_waves(tasks)
    assert len(waves) == 2
    assert len(waves[1]) == 2
    assert len(waves[2]) == 1


@pytest.mark.asyncio
async def test_execute_wave(mock_db):
    scheduler = TaskScheduler(mock_db)
    with patch.object(scheduler, "_execute_single_task", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = Task(name="test", status="completed")
        task = Task(name="test", project_id=uuid.uuid4())
        await scheduler._execute_wave([task])
        mock_exec.assert_called_once()
