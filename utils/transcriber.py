from typing import Optional, Any, List, Dict
from config import DEFAULT_MODEL, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE

_model_instance: Optional[Any] = None
_loaded_model_name: Optional[str] = None

def get_whisper_model(
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE
) -> Any:
    """
    Lazy-loads and caches the WhisperModel instance.
    Both the faster_whisper library and model weights are loaded on demand.
    """
    global _model_instance, _loaded_model_name

    if _model_instance is None or _loaded_model_name != model_name:
        from faster_whisper import WhisperModel
        _model_instance = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        _loaded_model_name = model_name

    return _model_instance

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
    """
    model = get_whisper_model(model_name=model_name, device=device, compute_type=compute_type)

    kwargs = {}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(audio_path, **kwargs)

    segment_list = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            segment_list.append({
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text
            })

    return segment_list

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