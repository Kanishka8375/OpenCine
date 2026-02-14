from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import Base, engine, get_db
from app.core.logging import setup_logging
from app.models import RenderJob
from app.schemas import CreateRenderRequest, CreateRenderResponse, JobStatusResponse
from celery_worker import render_video_task

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)


@app.post('/v1/renders', response_model=CreateRenderResponse)
async def create_render(payload: CreateRenderRequest, db: Session = Depends(get_db)):
    task = render_video_task.delay(payload.prompt, payload.face_reference_image)
    job = RenderJob(
        celery_task_id=task.id,
        prompt=payload.prompt,
        status='queued',
    )
    db.add(job)
    db.commit()
    return CreateRenderResponse(job_id=task.id, status='queued')


@app.get('/v1/renders/{job_id}', response_model=JobStatusResponse)
async def get_render(job_id: str, db: Session = Depends(get_db)):
    job = db.query(RenderJob).filter(RenderJob.celery_task_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return JobStatusResponse(job_id=job_id, status=job.status, output_url=job.output_url)


@app.get('/healthz')
async def healthcheck():
    return {'status': 'ok', 'instance': str(uuid.uuid4())}
