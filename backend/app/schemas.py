from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateRenderRequest(BaseModel):
    prompt: str = Field(min_length=10)
    face_reference_image: str | None = None


class CreateRenderResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    output_url: str | None = None


class Scene(BaseModel):
    scene_id: int
    visual_prompt: str
    dialogue: str
    shot_type: Literal['wide', 'medium', 'close-up'] | str
