from __future__ import annotations

import logging
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


class Stitcher:
    def concat_with_crossfade(self, video_paths: list[Path], output_path: Path, transition: float = 0.5) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info('Stitching %s clips with crossfade=%s', len(video_paths), transition)
        if len(video_paths) == 1:
            (
                ffmpeg.input(str(video_paths[0]))
                .output(str(output_path), c='copy')
                .overwrite_output()
                .run(quiet=True)
            )
            return output_path

        stream = ffmpeg.input(str(video_paths[0]))
        for idx, path in enumerate(video_paths[1:], start=1):
            nxt = ffmpeg.input(str(path))
            stream = ffmpeg.filter([stream, nxt], 'xfade', transition='fade', duration=transition, offset=idx * 4)

        ffmpeg.output(stream, str(output_path), vcodec='libx264', pix_fmt='yuv420p').overwrite_output().run(quiet=True)
        return output_path

    def mix_audio(self, video_path: Path, audio_paths: list[Path], output_path: Path) -> Path:
        logger.info('Mixing %s audio tracks into %s', len(audio_paths), video_path)
        if not audio_paths:
            return video_path

        audio_streams = [ffmpeg.input(str(a)).audio for a in audio_paths]
        mixed = ffmpeg.filter(audio_streams, 'amix', inputs=len(audio_paths), dropout_transition=0)
        (
            ffmpeg.output(
                ffmpeg.input(str(video_path)).video,
                mixed,
                str(output_path),
                vcodec='copy',
                acodec='aac',
                shortest=None,
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path


stitcher = Stitcher()
