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

def split_audio_into_chunks(audio_path: str, chunk_duration_sec: int, overlap_sec: float = 1.5) -> List[Dict[str, Any]]:
    """
    Splits an audio file into chunks of `chunk_duration_sec` seconds with `overlap_sec` overlap.
    Returns a list of dictionaries with chunk file path, start offset, and duration.
    """
    total_duration = get_audio_duration(audio_path)
    if total_duration <= 0 or total_duration <= chunk_duration_sec:
        return [{"chunk_path": audio_path, "start_offset": 0.0, "duration": total_duration, "is_temp": False}]

    chunks = []
    current_start = 0.0
    step = max(1.0, float(chunk_duration_sec) - float(overlap_sec))

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

        if current_start + duration >= total_duration:
            break

        current_start += step

    return chunks

def merge_chunk_segments(chunk_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges transcribed segments from multiple audio chunks with overlap, adjusting segment
    timestamps relative to the original audio file start and removing duplicate boundary segments.
    """
    raw_segments = []

    for item in chunk_results:
        offset = item.get("start_offset", 0.0)
        segments = item.get("segments", [])

        for seg in segments:
            raw_segments.append({
                "start": round(float(seg["start"]) + offset, 2),
                "end": round(float(seg["end"]) + offset, 2),
                "text": seg["text"].strip()
            })

    if not raw_segments:
        return []

    # Sort primarily by start timestamp
    raw_segments.sort(key=lambda s: (s["start"], s["end"]))

    merged_segments = []
    for seg in raw_segments:
        if not seg["text"]:
            continue

        if not merged_segments:
            merged_segments.append(seg)
            continue

        prev_seg = merged_segments[-1]

        # Check for duplicate segment resulting from chunk overlap
        is_duplicate = False
        if abs(seg["start"] - prev_seg["start"]) < 3.0 or seg["start"] < prev_seg["end"]:
            if seg["text"].lower() == prev_seg["text"].lower():
                is_duplicate = True
            elif seg["text"].lower() in prev_seg["text"].lower():
                is_duplicate = True
            elif prev_seg["text"].lower() in seg["text"].lower() and seg["start"] <= prev_seg["start"] + 1.0:
                merged_segments[-1] = seg
                is_duplicate = True

        if not is_duplicate:
            merged_segments.append(seg)

    return merged_segments

