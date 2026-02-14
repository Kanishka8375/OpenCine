from __future__ import annotations

import logging
import wave
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class DialogueAudioGenerator:
    """F5-TTS wrapper with graceful fallback when package isn't available."""

    def __init__(self) -> None:
        self._f5 = None
        try:
            from f5_tts.api import F5TTS  # type: ignore

            self._f5 = F5TTS()
            logger.info('Initialized F5-TTS engine')
        except ModuleNotFoundError:
            logger.warning('F5-TTS not installed; using silence fallback wav generator')
        except Exception:
            logger.exception('F5-TTS initialization failed; using silence fallback wav generator')

    def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info('Generating dialogue audio at %s', output_path)
        if self._f5 is not None:
            self._f5.infer(text=text, output_path=str(output_path))
            return output_path

        sr = 22050
        duration = max(2, min(15, len(text) // 12))
        samples = np.zeros(sr * duration, dtype=np.int16)
        with wave.open(str(output_path), 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes(samples.tobytes())
        return output_path


audio_generator = DialogueAudioGenerator()
