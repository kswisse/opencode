from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
from clippy_database import create_engine, get_session
from clippy_database.models.transcript import TranscriptModel
from clippy_database.models.segment import ConversationSegmentModel
from sqlalchemy import select
import uuid
from datetime import datetime


class SegmentActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="segment_conversation")
    async def execute(self, video_id: str) -> dict:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(
                select(TranscriptModel).where(TranscriptModel.video_id == video_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript or not transcript.segments:
                return {"video_id": video_id, "segments": []}

            raw_segments = transcript.segments if isinstance(transcript.segments, list) else []
            created = []
            for seg in raw_segments:
                model = ConversationSegmentModel(
                    id=uuid.uuid4(),
                    video_id=video_id,
                    start_time=seg.get("start", 0),
                    end_time=seg.get("end", 0),
                    text=seg.get("text", ""),
                    speaker_id=seg.get("speaker_id"),
                )
                db.add(model)
                created.append({
                    "id": str(model.id),
                    "start": model.start_time,
                    "end": model.end_time,
                    "text": model.text,
                })
            await db.commit()

        return {"video_id": video_id, "segments": created}
