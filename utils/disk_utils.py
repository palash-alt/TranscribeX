import os
import shutil
from typing import Tuple

# Default safety buffer as a fraction of required space (e.g., 0.20 for 20%)
SAFETY_BUFFER_FACTOR = 0.20


def estimate_required_temp_space(input_duration_seconds: float, chunk_duration_seconds: float, output_wav_bitrate_kbps: int = 128) -> float:
    """Estimate the total temporary disk space needed (in megabytes) for processing.

    The estimate includes:
    * Extracted audio file size (approximate bitrate * duration)
    * All chunk files (same size as original audio split into N chunks)
    * A safety buffer.

    Args:
        input_duration_seconds: Total duration of the input video/audio.
        chunk_duration_seconds: Desired length of each audio chunk.
        output_wav_bitrate_kbps: Approximate bitrate for the intermediate WAV files.

    Returns:
        Required space in megabytes (including safety buffer).
    """
    wav_size_kb = (output_wav_bitrate_kbps * input_duration_seconds) / 8.0
    wav_size_mb = wav_size_kb / 1024.0
    total_needed_mb = wav_size_mb * 2
    total_needed_mb *= (1 + SAFETY_BUFFER_FACTOR)
    return total_needed_mb


def has_sufficient_disk_space(required_mb: float, path: str = os.getcwd()) -> bool:
    """Check if the given path has at least ``required_mb`` free space.

    Args:
        required_mb: Required free space in megabytes.
        path: Directory to check (defaults to current working directory).
    """
    total, used, free = shutil.disk_usage(path)
    free_mb = free / (1024 * 1024)
    return free_mb >= required_mb


def verify_disk_space(input_duration_seconds: float, chunk_duration_seconds: float, path: str = os.getcwd()) -> Tuple[bool, str]:
    """Convenience wrapper that estimates required space and verifies availability.

    Returns:
        (True, "") if sufficient, otherwise (False, error_message).
    """
    required = estimate_required_temp_space(input_duration_seconds, chunk_duration_seconds)
    if not has_sufficient_disk_space(required, path):
        err = f"Insufficient disk space: required ~{required:.1f} MB free in '{path}'."
        return False, err
    return True, ""
