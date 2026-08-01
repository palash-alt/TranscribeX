def is_valid_transcript(text: str) -> bool:
    """
    Validates if transcript contains meaningful speech.
    Requires at least 5 words and at least 3 unique words.
    """
    if not text or not isinstance(text, str):
        return False

    words = text.strip().split()
    if len(words) < 5:
        return False

    unique_words = len(set(words))
    if unique_words < 3:
        return False

    return True

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
