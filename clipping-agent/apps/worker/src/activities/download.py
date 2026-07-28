import os
import subprocess
import tempfile
from pathlib import Path
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
from clippy_database import create_engine, get_session
from clippy_database.models.video import VideoModel
from sqlalchemy import select


class DownloadActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="download_video")
    async def execute(self, video_id: str) -> dict:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(select(VideoModel).where(VideoModel.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                raise ValueError(f"Video {video_id} not found")

            if video.source_url:
                with tempfile.TemporaryDirectory() as tmpdir:
                    import uuid
                    local_id = uuid.uuid4()
                    output_path = os.path.join(tmpdir, f"{local_id}.mp4")
                    subprocess.run(
                        ["yt-dlp", "-f", "best", "-o", output_path, video.source_url],
                        check=True, capture_output=True, text=True, timeout=7200,
                    )
                    storage_key = f"raw-videos/{video_id}.mp4"
                    await self.storage.upload("raw-videos", storage_key, output_path)
                    video.storage_key = storage_key
                    await db.commit()

        return {"video_id": video_id, "status": "downloaded"}
