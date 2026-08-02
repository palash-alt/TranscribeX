import subprocess
import shutil
import os
from utils.temp_manager import get_temp_audio_path
from utils.logger import get_logger

logger = get_logger()

def is_ffmpeg_available() -> bool:
    """
    Performs deep health check verifying FFmpeg executable is present and responsive.
    """
    if shutil.which("ffmpeg") is None:
        return False
    try:
        res = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        return res.returncode == 0
    except Exception as e:
        logger.warning(f"FFmpeg health check failed: {str(e)}")
        return False

def check_ffmpeg_installed() -> None:
    """Raises RuntimeError if ffmpeg is missing or unresponsive."""
    if not is_ffmpeg_available():
        msg = "FFmpeg executable is not functional or missing on system PATH."
        logger.error(msg)
        raise RuntimeError(
            "FFmpeg executable not found or broken on system PATH.\n"
            "Please install FFmpeg and add it to your system PATH."
        )

def extract_audio(video_path: str, output_audio_path: str = None) -> str:
    """
    Extracts audio track from a video file using FFmpeg.
    Returns path to the generated audio file.
    """
    check_ffmpeg_installed()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video file not found: {video_path}")

    if not output_audio_path:
        output_audio_path = get_temp_audio_path(".wav")

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            output_audio_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg extraction failed:\n{result.stderr.strip() if result.stderr else 'Unknown error'}")

    return output_audio_path