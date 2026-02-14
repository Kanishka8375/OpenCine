from __future__ import annotations

import logging
import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError
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
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


def _initialize_database_schema() -> None:
    """Try to create DB schema and keep API process alive on connectivity errors."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Database schema initialization complete')
    except SQLAlchemyError:
        logger.exception(
            'Database initialization failed; API will start but DB-backed routes may fail '
            'until DB is reachable'
        )


@app.on_event('startup')
def startup_init() -> None:
    _initialize_database_schema()

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)


@app.post('/v1/renders', response_model=CreateRenderResponse)
async def create_render(payload: CreateRenderRequest, db: Session = Depends(get_db)):
    task = render_video_task.delay(payload.prompt, payload.face_reference_image)
    job = RenderJob(celery_task_id=task.id, prompt=payload.prompt, status='queued')
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
