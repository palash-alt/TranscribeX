import os

def save_transcript_to_file(text: str, file_path: str) -> bool:
    """
    Saves the transcript text to the specified file path.
    Returns True on success, False otherwise.
    """
    if not text or not file_path:
        return False

    try:
        dirname = os.path.dirname(file_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        raise IOError(f"Failed to save file: {str(e)}")
