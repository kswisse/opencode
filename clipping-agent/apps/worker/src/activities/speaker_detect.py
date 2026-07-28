from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class SpeakerDetectActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="detect_speakers")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Detecting speakers for video {video_id}")
        return {"video_id": video_id, "speakers": []}
