import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from config import SUPPORTED_VIDEO_TYPES, SUPPORTED_EXPORT_FORMATS, PRIMARY_LANGUAGES, ALL_WHISPER_LANGUAGES
import os
from utils.extractor import extract_audio, is_ffmpeg_available
from utils.transcriber import transcribe_video_segments_with_retry, CancellationError
from utils.transcript_validator import is_valid_transcript, get_transcript_warning, get_validation_error_message
from utils.exporter import save_transcript_to_file
from utils.temp_manager import cleanup_file, cleanup_output_dir
from utils.performance_manager import detect_optimal_hardware_config
from utils.chunk_manager import split_audio_into_chunks, merge_chunk_segments, get_audio_duration
from utils.resource_manager import get_resource_snapshot, calculate_eta, check_sufficient_disk_space
from utils.logger import get_logger
from utils.disk_utils import verify_disk_space
from utils.ui_dialogs import show_error, show_info

logger = get_logger()
cancel_requested, current_segments = False, []

ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("920x720")
app.title("Transcript Generator v2.4")

def safe_gui(widget_func, *args, **kwargs):
    app.after(0, lambda: widget_func(*args, **kwargs))

# --- Resource Monitor Panel ---
res_frame = ctk.CTkFrame(app)
res_frame.pack(pady=5, padx=20, fill="x")

sys_metrics_lbl = ctk.CTkLabel(res_frame, text="CPU: --%  |  RAM: --% (-- GB Free)  |  Disk: -- GB Free", font=("Segoe UI", 12, "bold"))
sys_metrics_lbl.pack(pady=4)

DEFAULT_TASK_METRICS = "Chunk: --/--  |  ETA: --m --s  |  Model: --  |  Lang: Auto Detect"

task_metrics_lbl = ctk.CTkLabel(res_frame, text=DEFAULT_TASK_METRICS, font=("Segoe UI", 11))
# Progress UI
progress_frame = ctk.CTkFrame(app)
progress_frame.pack(pady=5, padx=20, fill="x")
progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="indeterminate")
progress_bar.pack(pady=2, fill="x")
progress_percent_lbl = ctk.CTkLabel(progress_frame, text="Preparing transcription...", font=("Segoe UI", 11))
progress_percent_lbl.pack()
task_metrics_lbl.pack(pady=2)

def update_sys_metrics_ui():
    snap = get_resource_snapshot()
    sys_metrics_lbl.configure(
        text=f"CPU: {snap['cpu_percent']}%  |  RAM: {snap['ram_percent']}% ({snap['ram_free_gb']} GB Free)  |  Disk: {snap['disk_free_gb']} GB Free"
    )
    app.after(1000, update_sys_metrics_ui)

app.after(500, update_sys_metrics_ui)

# --- Controls Frame (Language Selector) ---
controls_frame = ctk.CTkFrame(app)
controls_frame.pack(pady=5, padx=20, fill="x")

ctk.CTkLabel(controls_frame, text="Language:").grid(row=0, column=0, padx=10, pady=5)
primary_lang_map = {name: code for name, code in PRIMARY_LANGUAGES}
other_lang_map = {name: code for name, code in ALL_WHISPER_LANGUAGES}

def on_primary_lang_change(choice):
    if choice == "Other...":
        secondary_lang_dropdown.grid(row=0, column=2, padx=10, pady=5)
    else:
        secondary_lang_dropdown.grid_remove()

primary_lang_dropdown = ctk.CTkOptionMenu(controls_frame, values=[name for name, _ in PRIMARY_LANGUAGES], command=on_primary_lang_change)
primary_lang_dropdown.set("Auto Detect")
primary_lang_dropdown.grid(row=0, column=1, padx=10, pady=5)

secondary_lang_dropdown = ctk.CTkOptionMenu(controls_frame, values=[name for name, _ in ALL_WHISPER_LANGUAGES])
secondary_lang_dropdown.set("Spanish")
secondary_lang_dropdown.grid(row=0, column=2, padx=10, pady=5)
secondary_lang_dropdown.grid_remove()

def get_selected_language_name_and_code():
    selected_primary = primary_lang_dropdown.get()
    if selected_primary == "Other...":
        name = secondary_lang_dropdown.get()
        return name, other_lang_map.get(name, None)
    return selected_primary, primary_lang_map.get(selected_primary, None)

textbox = ctk.CTkTextbox(app, width=870, height=380)
textbox.pack(pady=5)

status = ctk.CTkLabel(app, text="Ready")
status.pack(pady=2)

def reset_job_ui(has_valid_transcript: bool = False):
    """
    Resets job-specific UI state (chunk counts, ETA, active model display, action buttons)
    to idle while preserving continuous system metrics polling.
    """
    safe_gui(task_metrics_lbl.configure, text=DEFAULT_TASK_METRICS)
    safe_gui(button.configure, state="normal", text="Select Video")
    safe_gui(cancel_button.configure, state="disabled")
    safe_gui(save_button.configure, state="normal" if has_valid_transcript else "disabled")
    # Clear selected file label on reset
    safe_gui(selected_file_label.configure, text="")
    # Reset progress UI
    safe_gui(progress_bar.stop)
    safe_gui(progress_bar.config, mode="indeterminate")
    safe_gui(progress_percent_lbl.configure, text="Ready")
    # After a short delay, show ready status
    safe_gui(app.after, 1500, lambda: status.configure(text="Ready"))

def cancel_process():
    global cancel_requested
    cancel_requested = True
    logger.info("User requested process cancellation.")
    # Clear selected file label on cancel
    safe_gui(selected_file_label.configure, text="")

def check_cancel():
    if cancel_requested:
        safe_gui(status.configure, text="❌ Transcription Cancelled")
        raise CancellationError("Operation Cancelled")

def process_video(file):
    global cancel_requested, current_segments
    cancel_requested, current_segments, temp_audio = False, [], None
    has_success = False

    safe_gui(button.configure, state="disabled", text="Processing...")
    safe_gui(cancel_button.configure, state="normal")
    safe_gui(save_button.configure, state="disabled")

    try:
        if not is_ffmpeg_available():
            logger.error("Pre-flight check failed: FFmpeg not available.")
            safe_gui(status.configure, text="❌ FFmpeg not found")
            safe_gui(textbox.delete, "1.0", "end")
            safe_gui(textbox.insert, "end", "Error: FFmpeg executable is not found or unresponsive on system PATH.")
            return

        perf_config = detect_optimal_hardware_config()
        lang_name, lang_code = get_selected_language_name_and_code()
        logger.info(f"Processing '{file}' using model '{perf_config['model_name']}' on {perf_config['device']}.")

        safe_gui(status.configure, text="⏳ Extracting audio...")
        # Show indeterminate progress while extracting audio
        safe_gui(progress_bar.start)
        safe_gui(progress_bar.config, mode="indeterminate")
        temp_audio = extract_audio(file)
        check_cancel()

        total_audio_duration = get_audio_duration(temp_audio)
        # Dynamic disk‑space verification based on actual duration and chunk size
        ok, err_msg = verify_disk_space(total_audio_duration, perf_config["chunk_duration"])
        if not ok:
            logger.error(f"Pre-flight check failed: {err_msg}")
            safe_gui(status.configure, text=f"❌ Error: {err_msg}")
            show_error("Disk Space Error", err_msg)
            return

        safe_gui(status.configure, text=f"⏳ Splitting audio for {perf_config['model_name']} engine...")
        chunks = split_audio_into_chunks(temp_audio, perf_config["chunk_duration"])
        # Switch progress bar to determinate for chunk processing
        safe_gui(progress_bar.stop)
        safe_gui(progress_bar.config, mode="determinate")
        safe_gui(progress_bar.configure, maximum=len(chunks))
        safe_gui(progress_percent_lbl.configure, text="0%")
        check_cancel()

        chunk_results, total_chunks, start_time = [], len(chunks), time.time()

        for idx, chunk in enumerate(chunks, start=1):
            check_cancel()
            elapsed = time.time() - start_time
            eta_str = calculate_eta(idx - 1, total_chunks, elapsed)

            safe_gui(task_metrics_lbl.configure, text=f"Chunk: {idx}/{total_chunks}  |  ETA: {eta_str}  |  Model: {perf_config['model_name']}  |  Lang: {lang_name}")
            safe_gui(status.configure, text=f"🎤 Transcribing chunk {idx}/{total_chunks} ({perf_config['model_name']} | {perf_config['device']})...")

            # Transcribe the current chunk with retry logic
            chunk_segments = transcribe_video_segments_with_retry(
                audio_path=chunk["chunk_path"],
                model_name=perf_config["model_name"],
                device=perf_config["device"],
                compute_type=perf_config["compute_type"],
                language=lang_code,
                max_retries=1
            )
            # Temporary diagnostics
            logger.debug(f"type(chunk_segments)={type(chunk_segments)} len={len(chunk_segments) if chunk_segments is not None else 'None'}")
            # Guard against unexpected None
            if chunk_segments is None:
                chunk_segments = []
            chunk_results.append({"start_offset": chunk["start_offset"], "segments": chunk_segments})
            if chunk.get("is_temp"):
                cleanup_file(chunk["chunk_path"])
                audio_path=chunk["chunk_path"],
                model_name=perf_config["model_name"],
                device=perf_config["device"],
                compute_type=perf_config["compute_type"],
                language=lang_code,
                max_retries=1
            )

            chunk_results.append({"start_offset": chunk["start_offset"], "segments": chunk_segments})
            if chunk.get("is_temp"):
                cleanup_file(chunk["chunk_path"])
            # Update determinate progress bar after each chunk
            safe_gui(progress_bar.configure, value=idx)
            percent = int(idx / total_chunks * 100)
            safe_gui(progress_percent_lbl.configure, text=f"{percent}%")

        check_cancel()
        merged_segments = merge_chunk_segments(chunk_results)
        transcript_text = "\n".join(s["text"] for s in merged_segments)

        if not is_valid_transcript(transcript_text, total_audio_duration):
            logger.warning("Transcript validation failed: No meaningful speech detected.")
            safe_gui(status.configure, text="❌ No meaningful speech detected.")
            safe_gui(textbox.delete, "1.0", "end")
            safe_gui(textbox.insert, "end", get_validation_error_message())
            return

        warning_msg = get_transcript_warning(transcript_text, total_audio_duration)
        status_suffix = f" ({warning_msg})" if warning_msg else ""

        current_segments = merged_segments
        has_success = True
        safe_gui(textbox.delete, "1.0", "end")
        safe_gui(textbox.insert, "end", transcript_text)
        safe_gui(status.configure, text=f"✅ Completed! ({perf_config['model_name']} model){status_suffix}")
        logger.info(f"Transcription completed successfully for '{file}'.")

    except CancellationError:
        logger.info("Transcription process cancelled successfully.")
        safe_gui(status.configure, text="❌ Transcription Cancelled")
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        safe_gui(status.configure, text="❌ Error")
        safe_gui(textbox.delete, "1.0", "end")
        safe_gui(textbox.insert, "end", str(e))
    finally:
        if temp_audio:
            cleanup_file(temp_audio)
        reset_job_ui(has_valid_transcript=has_success)

def open_video():
    file = filedialog.askopenfilename(filetypes=SUPPORTED_VIDEO_TYPES)
    if not file:
        return
    # Update selected file label
    display_name = truncate_filename(os.path.basename(file))
    safe_gui(selected_file_label.configure, text=display_name)
    threading.Thread(target=process_video, args=(file,), daemon=True).start()

def save_transcript():
    export_data = current_segments if current_segments else textbox.get("1.0", "end").strip()
    if not export_data:
        return

    file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=SUPPORTED_EXPORT_FORMATS)
    if file:
        try:
            save_transcript_to_file(export_data, file)
            show_info("Success", "Transcript saved successfully!")
        except Exception as e:
            show_error("Error", f"Failed to save transcript: {str(e)}")

button = ctk.CTkButton(app, text="Select Video", command=open_video)
button.pack()

save_button = ctk.CTkButton(app, text="Download Transcript", command=save_transcript, state="disabled")
save_button.pack(pady=5)

cancel_button = ctk.CTkButton(app, text="Cancel", command=cancel_process, state="disabled")
cancel_button.pack(pady=5)

def on_closing():
    cleanup_output_dir()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

def truncate_filename(name, max_len=30):
    return name if len(name) <= max_len else name[:max_len-3] + "..."

# Selected File label (initially empty)
selected_file_label = ctk.CTkLabel(app, text="", font=("Segoe UI", 11))
selected_file_label.pack(pady=2)

if __name__ == "__main__":
    app.mainloop()