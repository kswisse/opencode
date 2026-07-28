from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from uuid import UUID


@workflow.defn
class ClipPipelineWorkflow:
    @workflow.run
    async def run(self, video_id: UUID, tenant_id: UUID) -> dict:
        retry_policy = RetryPolicy(maximum_attempts=3)

        download_result = await workflow.execute_activity(
            "download_video",
            video_id,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry_policy,
        )

        transcript = await workflow.execute_activity(
            "transcribe_audio",
            video_id,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry_policy,
        )

        scenes = await workflow.execute_activity(
            "detect_scenes",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        speakers = await workflow.execute_activity(
            "detect_speakers",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        segments = await workflow.execute_activity(
            "segment_conversation",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        analysis = await workflow.execute_activity(
            "llm_analyze",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        candidates = await workflow.execute_activity(
            "score_segments",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        return {"video_id": str(video_id), "candidates": candidates}
