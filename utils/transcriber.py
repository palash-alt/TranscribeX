from typing import Optional
from faster_whisper import WhisperModel
from config import DEFAULT_MODEL, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE

_model_instance: Optional[WhisperModel] = None
_loaded_model_name: Optional[str] = None

def get_whisper_model(
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE
) -> WhisperModel:
    """
    Lazy-loads and caches the WhisperModel instance.
    The model is initialized on demand when first requested.
    """
    global _model_instance, _loaded_model_name

    if _model_instance is None or _loaded_model_name != model_name:
        _model_instance = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        _loaded_model_name = model_name

    return _model_instance

def transcribe_video(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE
) -> str:
    """
    Transcribes audio file using lazy-loaded Whisper model.
    """
    model = get_whisper_model(model_name=model_name, device=device, compute_type=compute_type)
    segments, info = model.transcribe(audio_path)

    text_list = [segment.text.strip() for segment in segments if segment.text.strip()]
    return "\n".join(text_list)