from typing import Optional

def is_valid_transcript(text: str, audio_duration: float = 0.0) -> bool:
    """
    Validates if transcript contains meaningful speech.
    Supports short audio clips (<15s) with relaxed word count rules.
    """
    if not text or not isinstance(text, str):
        return False

    words = text.strip().split()
    if not words:
        return False

    # Short audio clips (< 15 seconds) allow shorter speech
    if 0.0 < audio_duration <= 15.0:
        return len(words) >= 1

    # Standard / longer recording validation
    if len(words) < 5:
        return False

    unique_words = len(set(words))
    if unique_words < 3:
        return False

    return True

def get_transcript_warning(text: str, audio_duration: float = 0.0) -> Optional[str]:
    """
    Returns a non-blocking warning string if transcript is unusually brief.
    """
    if not text or not isinstance(text, str):
        return None

    words = text.strip().split()
    if len(words) < 5:
        return "⚠️ Note: Short transcript detected (< 5 words)."

    return None

def get_validation_error_message() -> str:
    """Returns a user-friendly string explaining potential transcript failure causes."""
    return (
        "Unable to generate a valid transcript.\n\n"
        "Possible reasons:\n"
        "- Poor audio quality\n"
        "- Background noise\n"
        "- Music instead of speech\n"
        "- Unsupported language or silent audio"
    )

