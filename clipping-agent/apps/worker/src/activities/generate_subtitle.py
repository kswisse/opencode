from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class GenerateSubtitleActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="generate_subtitle")
    async def execute(self, clip_key: str, segments: list[dict]) -> dict:
        activity.logger.info(f"Generating subtitles for {clip_key}")
        return {"clip_key": clip_key, "subtitle_key": clip_key.replace(".mp4", ".srt")}
