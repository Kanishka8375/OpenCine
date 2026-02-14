from __future__ import annotations

import json
import logging
from typing import Any

import requests
from transformers import AutoTokenizer, pipeline

from app.core.config import get_settings
from app.schemas import Scene

logger = logging.getLogger(__name__)
settings = get_settings()


class ScriptDirector:
    def __init__(self) -> None:
        self._tokenizer = None
        self._pipe = None

    def _local_pipeline(self):
        if self._pipe is None:
            logger.info('Loading local screenplay model %s', settings.llm_model_id)
            self._tokenizer = AutoTokenizer.from_pretrained(settings.llm_model_id)
            self._pipe = pipeline(
                'text-generation',
                model=settings.llm_model_id,
                tokenizer=self._tokenizer,
                device_map='auto',
            )
        return self._pipe

    def generate_screenplay(self, prompt: str) -> list[Scene]:
        logger.info('Generating screenplay for prompt length=%s', len(prompt))
        system_prompt = (
            'Return ONLY valid JSON. Output a list of scenes with fields '
            'scene_id, visual_prompt, dialogue, shot_type (wide|medium|close-up).'
        )
        user_prompt = f'{system_prompt}\n\nUser request: {prompt}'

        if settings.llm_api_url:
            logger.info('Calling external LLM API endpoint for screenplay generation')
            payload: dict[str, Any] = {'model': settings.llm_model_id, 'prompt': user_prompt}
            headers = {'Authorization': f'Bearer {settings.llm_api_key}'} if settings.llm_api_key else {}
            response = requests.post(settings.llm_api_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            raw_text = response.json().get('text', '[]')
        else:
            local_pipe = self._local_pipeline()
            output = local_pipe(user_prompt, max_new_tokens=1200, temperature=0.3, do_sample=False)
            raw_text = output[0]['generated_text']

        json_start = raw_text.find('[')
        json_end = raw_text.rfind(']') + 1
        candidate = raw_text[json_start:json_end]
        scenes_raw = json.loads(candidate)
        scenes = [Scene.model_validate(scene) for scene in scenes_raw]
        logger.info('Generated %s screenplay scenes', len(scenes))
        return scenes


director = ScriptDirector()
