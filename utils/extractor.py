import subprocess
import shutil
import os
from utils.temp_manager import get_temp_audio_path

def is_ffmpeg_available() -> bool:
    """Checks if ffmpeg executable is installed and available on system PATH."""
    return shutil.which("ffmpeg") is not None

def check_ffmpeg_installed() -> None:
    """Raises RuntimeError if ffmpeg is missing from PATH."""
    if not is_ffmpeg_available():
        raise RuntimeError(
            "FFmpeg executable not found on system PATH.\n"
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