import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from clippy_config import ClippyConfig
from clippy_logging import setup_logging, get_logger
from clippy_database import create_engine, get_session
from clippy_storage import create_storage
from clippy_events import NATSClient
from clippy_vectordb import VectorDB

from .workflows.clip_pipeline import ClipPipelineWorkflow
from .activities.download import DownloadActivity
from .activities.transcribe import TranscribeActivity
from .activities.scene_detect import SceneDetectActivity
from .activities.speaker_detect import SpeakerDetectActivity
from .activities.segment import SegmentActivity
from .activities.llm_analyze import LLMAnalyzeActivity
from .activities.score import ScoreActivity
from .activities.generate_clip import GenerateClipActivity
from .activities.generate_subtitle import GenerateSubtitleActivity


async def main():
    config = ClippyConfig()
    setup_logging(config.environment)
    logger = get_logger("clippy-worker")

    engine = create_engine(config.database.dsn)
    db_session = get_session(engine)

    storage = create_storage(
        provider=config.storage.provider,
        endpoint=config.storage.endpoint,
        access_key=config.storage.access_key,
        secret_key=config.storage.secret_key,
    )

    nats = NATSClient(config.nats.servers)
    await nats.connect()

    vectordb = VectorDB(config.qdrant.host, config.qdrant.port, config.qdrant.collection)
    await vectordb.ensure_collection()

    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    activities = [
        DownloadActivity(storage, nats, config),
        TranscribeActivity(storage, nats, config),
        SceneDetectActivity(storage, nats, config),
        SpeakerDetectActivity(storage, nats, config),
        SegmentActivity(storage, nats, config),
        LLMAnalyzeActivity(storage, nats, config),
        ScoreActivity(storage, nats, config, vectordb),
        GenerateClipActivity(storage, nats, config),
        GenerateSubtitleActivity(storage, nats, config),
    ]

    worker = Worker(
        client=client,
        task_queue=config.temporal.task_queue,
        workflows=[ClipPipelineWorkflow],
        activities=[a.execute for a in activities],
    )

    logger.info("worker_started", task_queue=config.temporal.task_queue)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
