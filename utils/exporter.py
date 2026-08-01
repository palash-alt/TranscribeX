import os
from typing import List, Dict, Any, Union

def format_timestamp(seconds: float, is_vtt: bool = False) -> str:
    """
    Formats floating-point seconds into standard subtitle timestamp.
    SRT format: HH:MM:SS,mmm
    VTT format: HH:MM:SS.mmm
    """
    total_milliseconds = int(round(seconds * 1000))
    hours = total_milliseconds // 3600000
    total_milliseconds %= 3600000
    minutes = total_milliseconds // 60000
    total_milliseconds %= 60000
    secs = total_milliseconds // 1000
    millis = total_milliseconds % 1000

    sep = "." if is_vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"

def export_to_srt(segments: List[Dict[str, Any]]) -> str:
    """Formats segments list into SubRip (.srt) subtitle format."""
    blocks = []
    for idx, seg in enumerate(segments, start=1):
        start_str = format_timestamp(seg.get("start", 0.0), is_vtt=False)
        end_str = format_timestamp(seg.get("end", 0.0), is_vtt=False)
        text = seg.get("text", "")
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{text}")
    return "\n\n".join(blocks)

def export_to_vtt(segments: List[Dict[str, Any]]) -> str:
    """Formats segments list into WebVTT (.vtt) subtitle format."""
    blocks = ["WEBVTT\n"]
    for idx, seg in enumerate(segments, start=1):
        start_str = format_timestamp(seg.get("start", 0.0), is_vtt=True)
        end_str = format_timestamp(seg.get("end", 0.0), is_vtt=True)
        text = seg.get("text", "")
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{text}")
    return "\n\n".join(blocks)

def export_to_txt(data: Union[str, List[Dict[str, Any]]]) -> str:
    """Formats segments list or string into plain text format."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return "\n".join(seg.get("text", "") for seg in data if "text" in seg)
    return str(data)

def save_transcript_to_file(data: Union[str, List[Dict[str, Any]]], file_path: str) -> bool:
    """
    Saves transcript data (segments list or plain text) to the specified file path.
    Auto-detects file extension (.txt, .srt, .vtt) and applies appropriate formatting.
    """
    if data is None or not file_path:
        return False

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".srt" and isinstance(data, list):
        content = export_to_srt(data)
    elif ext == ".vtt" and isinstance(data, list):
        content = export_to_vtt(data)
    else:
        content = export_to_txt(data)

    try:
        dirname = os.path.dirname(file_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        raise IOError(f"Failed to save file: {str(e)}")
