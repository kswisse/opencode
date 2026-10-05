#!/usr/bin/env python3
"""
ARQ Worker Runner Script

This script starts the ARQ worker to process background jobs.

Usage:
    python -m src.worker.run_worker
    
Or with arq command:
    arq src.worker.arq_worker.WorkerSettings
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.worker.arq_worker import WorkerSettings


async def main():
    """Main entry point for the worker."""
    from arq import run_worker
    
    print("Starting ARQ Worker...")
    print(f"Redis URL: {WorkerSettings.redis_settings}")
    print(f"Max Jobs: {WorkerSettings.max_jobs}")
    print(f"Job Timeout: {WorkerSettings.job_timeout}s")
    
    await run_worker(WorkerSettings)


if __name__ == "__main__":
    asyncio.run(main())
