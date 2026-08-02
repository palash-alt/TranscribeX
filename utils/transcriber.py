from typing import Optional, Any, List, Dict, Tuple
from config import DEFAULT_MODEL, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE

class CancellationError(Exception):
    """Exception raised when a transcription process is cancelled by the user."""
    pass

_model_instance: Optional[Any] = None
_loaded_model_key: Optional[Tuple[str, str, str]] = None

def get_whisper_model(
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE
) -> Any:
    """
    Lazy-loads and caches the WhisperModel instance.
    Both the faster_whisper library and model weights are loaded on demand.
    Keyed by (model_name, device, compute_type) tuple.
    """
    global _model_instance, _loaded_model_key

    current_key = (model_name, device, compute_type)
    if _model_instance is None or _loaded_model_key != current_key:
        from faster_whisper import WhisperModel
        _model_instance = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        _loaded_model_key = current_key

    return _model_instance
from utils.logger import get_logger

logger = get_logger()

def transcribe_video_segments(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Primary transcription method. Returns structured segment list containing
    timestamp metadata (start, end, text). Accepts optional language code.
    Includes automated GPU OOM fallback to CPU.
    """
    kwargs = {"vad_filter": True}
    if language:
        kwargs["language"] = language

    try:
        model = get_whisper_model(model_name=model_name, device=device, compute_type=compute_type)
        segments, info = model.transcribe(audio_path, **kwargs)
    except Exception as e:
        err_msg = str(e).lower()
        if device == "cuda" and ("out of memory" in err_msg or "cuda" in err_msg or "alloc" in err_msg):
            logger.warning(f"GPU OOM detected ({str(e)}). Falling back to CPU int8 engine.")
            model = get_whisper_model(model_name=model_name, device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, **kwargs)
        else:
            raise e

    segment_list = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            segment_list.append({
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text
            })

import time

def transcribe_video_segments_with_retry(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: Optional[str] = None,
    max_retries: int = 1
) -> List[Dict[str, Any]]:
    """
    Transcribes audio segments with automated single-retry on transient errors.
    """
    attempt = 0
    while True:
        try:
            return transcribe_video_segments(
                audio_path=audio_path,
                model_name=model_name,
                device=device,
                compute_type=compute_type,
                language=language
            )
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise e
            logger.warning(f"Chunk transcription attempt {attempt} failed ({str(e)}). Retrying once...")
            time.sleep(0.5)

def transcribe_video(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: Optional[str] = None
) -> str:
    """
    Backward-compatible wrapper converting segment metadata into plain text.
    """
    segments = transcribe_video_segments(
        audio_path,
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        language=language
    )
    return "\n".join(s["text"] for s in segments)