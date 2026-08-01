import os
import uuid
from config import OUTPUT_DIR

def get_temp_audio_path(extension: str = ".wav") -> str:
    """Generates a unique temporary audio file path inside OUTPUT_DIR."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"audio_{uuid.uuid4().hex[:8]}{extension}"
    return os.path.join(OUTPUT_DIR, filename)

def cleanup_file(file_path: str) -> None:
    """Safely removes a temporary file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

def cleanup_output_dir() -> None:
    """Cleans up leftover temporary audio files in OUTPUT_DIR."""
    if os.path.exists(OUTPUT_DIR):
        for item in os.listdir(OUTPUT_DIR):
            if item.startswith("audio_") and item.endswith(".wav"):
                cleanup_file(os.path.join(OUTPUT_DIR, item))
