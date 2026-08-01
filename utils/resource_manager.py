import shutil
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
