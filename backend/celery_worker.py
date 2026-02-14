from __future__ import annotations

import logging
import uuid
from pathlib import Path

import boto3
from celery import Celery

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models import RenderJob
from app.services.audio_gen import audio_generator
from app.services.image_gen import keyframe_generator
from app.services.llm_script import director
from app.services.stitcher import stitcher
from app.services.video_gen import scene_video_generator

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

celery = Celery('opencine', broker=settings.redis_url, backend=settings.redis_url)


def _update_status(task_id: str, status: str, output_url: str | None = None) -> None:
    db = SessionLocal()
    try:
        job = db.query(RenderJob).filter(RenderJob.celery_task_id == task_id).first()
        if not job:
            return
        job.status = status
        if output_url:
            job.output_url = output_url
        db.commit()
    finally:
        db.close()


@celery.task(bind=True, name='render_video_task')
def render_video_task(self, prompt: str, face_reference_image: str | None = None) -> dict[str, str]:
    task_id = self.request.id
    _update_status(task_id, 'processing')

    run_id = uuid.uuid4().hex[:10]
    work_dir = Path(settings.output_dir) / run_id
    work_dir.mkdir(parents=True, exist_ok=True)
    logger.info('Starting render task=%s work_dir=%s', task_id, work_dir)

    scenes = director.generate_screenplay(prompt)
    video_clips: list[Path] = []
    audio_tracks: list[Path] = []

    for scene in scenes:
        logger.info('Processing scene_id=%s', scene.scene_id)
        keyframe_path = work_dir / f'scene_{scene.scene_id:03d}.png'
        clip_path = work_dir / f'scene_{scene.scene_id:03d}.mp4'
        audio_path = work_dir / f'scene_{scene.scene_id:03d}.wav'

        keyframe_generator.generate_keyframe(
            scene_prompt=scene.visual_prompt,
            output_path=keyframe_path,
            face_reference_image=face_reference_image,
        )
        scene_video_generator.generate_video(scene.visual_prompt, keyframe_path, clip_path)
        audio_generator.synthesize(scene.dialogue, audio_path)

        video_clips.append(clip_path)
        audio_tracks.append(audio_path)

    stitched_video = stitcher.concat_with_crossfade(video_clips, work_dir / 'stitched.mp4')
    final_video = stitcher.mix_audio(stitched_video, audio_tracks, work_dir / 'final.mp4')

    s3_key = f'renders/{run_id}/final.mp4'
    s3 = boto3.client('s3', region_name=settings.s3_region)
    s3.upload_file(str(final_video), settings.s3_bucket, s3_key)
    output_url = f's3://{settings.s3_bucket}/{s3_key}'

    _update_status(task_id, 'completed', output_url=output_url)
    logger.info('Render task complete task=%s output=%s', task_id, output_url)
    return {'task_id': task_id, 'status': 'completed', 'output_url': output_url}
