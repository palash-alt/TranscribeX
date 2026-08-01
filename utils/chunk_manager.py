import subprocess
import shutil
import os
import wave
from typing import List, Dict, Any
from utils.temp_manager import get_temp_audio_path, cleanup_file

def get_audio_duration(audio_path: str) -> float:
    """
    Determines audio duration in seconds using ffprobe, wave header inspection, or ffmpeg fallback.
    """
    # 1. Try wave module for .wav files
    if audio_path.lower().endswith(".wav"):
        try:
            with wave.open(audio_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass

    # 2. Try ffprobe
    if shutil.which("ffprobe"):
        try:
            res = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return float(res.stdout.strip())
        except Exception:
            pass

    # 3. Fallback: Parse ffmpeg -i output
    try:
        res = subprocess.run(
            ["ffmpeg", "-i", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        pass

    return 0.0

def split_audio_into_chunks(audio_path: str, chunk_duration_sec: int) -> List[Dict[str, Any]]:
    """
    Splits an audio file into chunks of `chunk_duration_sec` seconds.
    Returns a list of dictionaries with chunk file path, start offset, and duration.
    """
    total_duration = get_audio_duration(audio_path)
    if total_duration <= 0 or total_duration <= chunk_duration_sec:
        return [{"chunk_path": audio_path, "start_offset": 0.0, "duration": total_duration, "is_temp": False}]

    chunks = []
    current_start = 0.0

    while current_start < total_duration:
        duration = min(float(chunk_duration_sec), total_duration - current_start)
        chunk_file = get_temp_audio_path(".wav")

        res = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss", str(current_start),
                "-i", audio_path,
                "-t", str(duration),
                "-c", "copy",
                chunk_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        if res.returncode != 0 or not os.path.exists(chunk_file):
            # Fallback without -c copy
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss", str(current_start),
                    "-i", audio_path,
                    "-t", str(duration),
                    chunk_file
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )

        chunks.append({
            "chunk_path": chunk_file,
            "start_offset": current_start,
            "duration": duration,
            "is_temp": True
        })

        current_start += duration

    return chunks

def merge_chunk_segments(chunk_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges transcribed segments from multiple audio chunks, adjusting segment
    timestamps relative to the original audio file start.
    """
    merged_segments = []

    for item in chunk_results:
        offset = item.get("start_offset", 0.0)
        segments = item.get("segments", [])

        for seg in segments:
            merged_segments.append({
                "start": float(seg["start"]) + offset,
                "end": float(seg["end"]) + offset,
                "text": seg["text"]
            })

    return merged_segments
