from __future__ import annotations

import logging
from pathlib import Path

import torch
from diffusers import FluxPipeline

from app.core.config import get_settings
from app.core.memory_manager import model_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class KeyframeGenerator:
    def __init__(self) -> None:
        model_manager.register_model('flux', self._build_flux)

    @staticmethod
    def _build_flux() -> FluxPipeline:
        logger.info('Loading Flux pipeline %s', settings.flux_model_id)
        pipe = FluxPipeline.from_pretrained(
            settings.flux_model_id,
            torch_dtype=torch.bfloat16,
        )
        try:
            pipe.load_ip_adapter(settings.ip_adapter_id)
            logger.info('Loaded IP-Adapter FaceID: %s', settings.ip_adapter_id)
        except Exception:
            logger.exception('IP-Adapter loading failed; continuing without face conditioning')
        pipe.enable_model_cpu_offload()
        return pipe

    def generate_keyframe(
        self,
        scene_prompt: str,
        output_path: Path,
        face_reference_image: str | None = None,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pipe = model_manager.load_model('flux')
        logger.info('Generating keyframe at %s', output_path)

        kwargs = {
            'prompt': scene_prompt,
            'num_inference_steps': 35,
            'guidance_scale': 4.0,
            'height': 1024,
            'width': 1024,
        }
        if face_reference_image:
            kwargs['ip_adapter_image'] = face_reference_image

        image = pipe(**kwargs).images[0]
        image.save(str(output_path))
        return output_path


keyframe_generator = KeyframeGenerator()
