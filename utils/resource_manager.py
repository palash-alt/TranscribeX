import shutil
import time
import psutil
from typing import Dict, Any, Tuple
from config import OUTPUT_DIR

# --- Existing snapshot utilities -------------------------------------------------

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Captures live CPU usage, RAM usage, available RAM in GB, and free disk space in GB.
    Cross-platform implementation powered by psutil and shutil.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_free_gb = round(mem.available / (1024 ** 3), 1)
        disk_usage = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR else ".")
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 1)
        return {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "ram_free_gb": ram_free_gb,
            "disk_free_gb": disk_free_gb,
        }
    except Exception:
        return {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_free_gb": 0.0,
            "disk_free_gb": 0.0,
        }

def calculate_eta(completed_chunks: int, total_chunks: int, elapsed_seconds: float) -> str:
    """
    Calculates estimated time remaining based on completed chunks and elapsed processing time.
    """
    if completed_chunks <= 0 or total_chunks <= 0 or completed_chunks >= total_chunks:
        return "00m 00s"
    avg_time_per_chunk = elapsed_seconds / completed_chunks
    remaining_chunks = total_chunks - completed_chunks
    eta_seconds = int(avg_time_per_chunk * remaining_chunks)
    hours = eta_seconds // 3600
    minutes = (eta_seconds % 3600) // 60
    seconds = eta_seconds % 60
    if hours > 0:
        return f"{hours:02d}h {minutes:02d}m"
    return f"{minutes:02d}m {seconds:02d}s"

def check_sufficient_disk_space(required_mb: float = 500.0) -> bool:
    """
    Legacy fixed‑threshold check (kept for backward compatibility).
    """
    try:
        disk_usage = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR else ".")
        free_mb = disk_usage.free / (1024 * 1024)
        return free_mb >= required_mb
    except Exception:
        return True

# --- New dynamic disk‑space utilities -------------------------------------------

DISK_SPACE_BUFFER_PCT = 0.20  # default safety buffer (20%)

def estimate_temp_space(input_seconds: float, chunk_duration_sec: int) -> int:
    """Estimate total temporary disk space needed for a transcription run.
    Assumes PCM WAV at ~0.084 MiB per second of audio.
    Returns required bytes.
    """
    wav_per_sec_bytes = int(0.084 * 1024 * 1024)  # ~88 KB per second
    import math
    chunk_cnt = math.ceil(input_seconds / chunk_duration_sec)
    # Add 10 % per‑file overhead for container metadata.
    per_chunk_est = int(wav_per_sec_bytes * chunk_duration_sec * 1.10)
    total_est = per_chunk_est * chunk_cnt
    total_est = int(total_est * (1 + DISK_SPACE_BUFFER_PCT))
    return total_est

def has_enough_disk_space(required_bytes: int) -> Tuple[bool, str]:
    """Check whether OUTPUT_DIR drive has enough free space.
    Returns (True, "") if sufficient; otherwise (False, error_message).
    """
    try:
        disk_usage = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR else ".")
        free_bytes = disk_usage.free
        if free_bytes >= required_bytes:
            return True, ""
        deficit_mb = (required_bytes - free_bytes) / (1024 * 1024)
        return False, f"Insufficient free disk space. Need an additional {deficit_mb:.1f} MiB."
    except Exception as e:
        return False, f"Disk space check failed: {str(e)}"

import time
import psutil
from typing import Dict, Any
from config import OUTPUT_DIR

def get_resource_snapshot() -> Dict[str, Any]:
    """
    Captures live CPU usage, RAM usage, available RAM in GB, and free disk space in GB.
    Cross-platform implementation powered by psutil and shutil.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_free_gb = round(mem.available / (1024 ** 3), 1)

        disk_usage = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR else ".")
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 1)

        return {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "ram_free_gb": ram_free_gb,
            "disk_free_gb": disk_free_gb,
        }
    except Exception:
        return {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_free_gb": 0.0,
            "disk_free_gb": 0.0,
        }

def calculate_eta(completed_chunks: int, total_chunks: int, elapsed_seconds: float) -> str:
    """
    Calculates estimated time remaining based on completed chunks and elapsed processing time.
    """
    if completed_chunks <= 0 or total_chunks <= 0 or completed_chunks >= total_chunks:
        return "00m 00s"

    avg_time_per_chunk = elapsed_seconds / completed_chunks
    remaining_chunks = total_chunks - completed_chunks
    eta_seconds = int(avg_time_per_chunk * remaining_chunks)

    hours = eta_seconds // 3600
    minutes = (eta_seconds % 3600) // 60
    seconds = eta_seconds % 60

    if hours > 0:
        return f"{hours:02d}h {minutes:02d}m"
    return f"{minutes:02d}m {seconds:02d}s"

def check_sufficient_disk_space(required_mb: float = 500.0) -> bool:
    """
    Verifies that the target output drive has at least `required_mb` of free storage space.
    """
    try:
        disk_usage = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR else ".")
        free_mb = disk_usage.free / (1024 * 1024)
        return free_mb >= required_mb
    except Exception:
        return True

