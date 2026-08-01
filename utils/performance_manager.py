import os
import psutil
from typing import Dict, Any

def get_system_memory_info() -> Dict[str, float]:
    """
    Returns total and available system RAM in Gigabytes using psutil (cross-platform).
    """
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        return {"total_gb": total_gb, "available_gb": available_gb}
    except Exception:
        # Cross-platform safe fallback
        return {"total_gb": 8.0, "available_gb": 4.0}

def is_cuda_available() -> bool:
    """Checks if CUDA GPU hardware acceleration is available via ctranslate2."""
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False

def get_adaptive_chunk_duration(available_ram_gb: float) -> int:
    """
    Calculates adaptive audio chunk duration in seconds based on available system RAM.
    - < 4 GB available: 120s (2 min chunks) - Low Memory Mode
    - 4 to 8 GB available: 300s (5 min chunks)
    - 8 to 16 GB available: 600s (10 min chunks)
    - > 16 GB available: 1200s (20 min chunks)
    """
    if available_ram_gb < 4.0:
        return 120
    elif available_ram_gb < 8.0:
        return 300
    elif available_ram_gb < 16.0:
        return 600
    else:
        return 1200

def detect_optimal_hardware_config() -> Dict[str, Any]:
    """
    Analyzes system resources (RAM, CPU cores, GPU) to auto-select
    the best Whisper model, device, compute type, and chunk size.
    """
    mem_info = get_system_memory_info()
    avail_ram = mem_info["available_gb"]
    total_ram = mem_info["total_gb"]
    cuda_supported = is_cuda_available()

    chunk_duration = get_adaptive_chunk_duration(avail_ram)
    is_low_mem = avail_ram < 4.0 or total_ram < 8.0

    if cuda_supported:
        device = "cuda"
        compute_type = "float16"
        model_name = "small" if total_ram >= 8.0 else "base"
    else:
        device = "cpu"
        compute_type = "int8"
        if total_ram < 4.0:
            model_name = "tiny"
        elif total_ram < 12.0:
            model_name = "base"
        else:
            model_name = "small"

    return {
        "model_name": model_name,
        "device": device,
        "compute_type": compute_type,
        "chunk_duration": chunk_duration,
        "is_low_mem": is_low_mem,
        "total_ram_gb": round(total_ram, 1),
        "available_ram_gb": round(avail_ram, 1),
    }
