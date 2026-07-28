from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
from clippy_vectordb import VectorDB
from clippy_database import create_engine, get_session
from clippy_database.models.segment import ConversationSegmentModel
from clippy_database.models.candidate import ClipCandidateModel
from sqlalchemy import select
import uuid


class ScoreActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig, vectordb: VectorDB):
        self.storage = storage
        self.nats = nats
        self.config = config
        self.vectordb = vectordb

    @activity.defn(name="score_segments")
    async def execute(self, video_id: str) -> list[dict]:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(
                select(ConversationSegmentModel).where(
                    ConversationSegmentModel.video_id == video_id
                ).order_by(ConversationSegmentModel.start_time)
            )
            segments = result.scalars().all()

            weights = self.config.scoring.weights
            min_duration = self.config.scoring.min_clip_duration
            max_duration = self.config.scoring.max_clip_duration

            candidates = []
            for seg in segments:
                duration = seg.end_time - seg.start_time
                if duration < min_duration or duration > max_duration:
                    continue

                text_len = len(seg.text or "")
                score = {
                    "virality": min(100, text_len * 0.5),
                    "retention": min(100, duration * 2),
                    "hook": min(100, text_len * 0.3),
                    "emotion": 50.0,
                    "shareability": min(100, text_len * 0.4),
                    "educational": 50.0,
                }

                predicted = sum(
                    score.get(k, 0) * w
                    for k, w in weights.items()
                ) / sum(weights.values())

                candidate = ClipCandidateModel(
                    id=uuid.uuid4(),
                    video_id=video_id,
                    segment_ids=[seg.id],
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    summary=(seg.text or "")[:100],
                    scores=score,
                    predicted_score=predicted,
                )
                db.add(candidate)
                candidates.append({
                    "id": str(candidate.id),
                    "start": candidate.start_time,
                    "end": candidate.end_time,
                    "score": predicted,
                })

            await db.commit()

        return candidates
