from __future__ import annotations

import logging
from pathlib import Path

import torch
from diffusers import HunyuanVideoPipeline, HunyuanVideoTransformer3DModel

from app.core.config import get_settings
from app.core.memory_manager import model_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class SceneVideoGenerator:
    def __init__(self) -> None:
        model_manager.register_model('hunyuan', self._build_hunyuan)

    @staticmethod
    def _build_hunyuan() -> HunyuanVideoPipeline:
        logger.info('Loading Hunyuan I2V pipeline %s', settings.hunyuan_model_id)
        transformer = HunyuanVideoTransformer3DModel.from_pretrained(
            settings.hunyuan_model_id,
            subfolder='transformer',
            torch_dtype=torch.bfloat16,
            load_in_4bit=True,
        )
        pipe = HunyuanVideoPipeline.from_pretrained(
            settings.hunyuan_model_id,
            transformer=transformer,
            torch_dtype=torch.bfloat16,
        )
        pipe.enable_model_cpu_offload()
        return pipe

    def generate_video(self, prompt: str, image_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pipe = model_manager.load_model('hunyuan')
        logger.info('Generating video for keyframe=%s', image_path)

        image = pipe.image_processor.load_image(str(image_path))
        result = pipe(
            prompt=prompt,
            image=image,
            num_frames=129,
            height=720,
            width=1280,
            num_inference_steps=40,
            guidance_scale=6.0,
        )
        frames = result.frames[0]
        pipe.export_to_video(frames, str(output_path), fps=24)
        return output_path


scene_video_generator = SceneVideoGenerator()
