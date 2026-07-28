import os
import subprocess
import tempfile
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class GenerateClipActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="generate_clip")
    async def execute(self, video_id: str, candidate_id: str, start_time: float, end_time: float) -> dict:
        activity.logger.info(f"Generating clip {candidate_id} from video {video_id}")
        return {"candidate_id": candidate_id, "clip_key": f"clips/{candidate_id}.mp4"}
