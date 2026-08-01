import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from config import (
    SUPPORTED_VIDEO_TYPES,
    SUPPORTED_EXPORT_FORMATS,
    PRIMARY_LANGUAGES,
    ALL_WHISPER_LANGUAGES,
)
from utils.extractor import extract_audio, is_ffmpeg_available
from utils.transcriber import transcribe_video_segments
from utils.transcript_validator import is_valid_transcript, get_validation_error_message
from utils.exporter import save_transcript_to_file
from utils.temp_manager import cleanup_file
from utils.performance_manager import detect_optimal_hardware_config
from utils.chunk_manager import split_audio_into_chunks, merge_chunk_segments
from utils.resource_manager import get_resource_snapshot, calculate_eta

cancel_requested = False
current_segments = []

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.geometry("920x720")
app.title("Transcript Generator v2.2 (Sprint 1)")

# Thread-safe GUI Dispatcher Helper
def safe_gui(widget_func, *args, **kwargs):
    app.after(0, lambda: widget_func(*args, **kwargs))

# --- Resource Monitor Panel ---
res_frame = ctk.CTkFrame(app)
res_frame.pack(pady=5, padx=20, fill="x")

sys_metrics_lbl = ctk.CTkLabel(
    res_frame,
    text="CPU: --%  |  RAM: --% (-- GB Free)  |  Disk: -- GB Free",
    font=("Segoe UI", 12, "bold")
)
sys_metrics_lbl.pack(pady=4)

task_metrics_lbl = ctk.CTkLabel(
    res_frame,
    text="Chunk: --/--  |  ETA: --m --s  |  Model: --  |  Lang: Auto Detect",
    font=("Segoe UI", 11)
)
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

lang_label = ctk.CTkLabel(controls_frame, text="Language:")
lang_label.grid(row=0, column=0, padx=10, pady=5)

primary_lang_map = {name: code for name, code in PRIMARY_LANGUAGES}
other_lang_map = {name: code for name, code in ALL_WHISPER_LANGUAGES}

def on_primary_lang_change(choice):
    if choice == "Other...":
        secondary_lang_dropdown.grid(row=0, column=2, padx=10, pady=5)
    else:
        secondary_lang_dropdown.grid_remove()

primary_lang_dropdown = ctk.CTkOptionMenu(
    controls_frame,
    values=[name for name, _ in PRIMARY_LANGUAGES],
    command=on_primary_lang_change
)
primary_lang_dropdown.set("Auto Detect")
primary_lang_dropdown.grid(row=0, column=1, padx=10, pady=5)

secondary_lang_dropdown = ctk.CTkOptionMenu(
    controls_frame,
    values=[name for name, _ in ALL_WHISPER_LANGUAGES]
)
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

def cancel_process():
    global cancel_requested
    cancel_requested = True

def check_cancel():
    if cancel_requested:
        safe_gui(status.configure, text="❌ Transcription Cancelled")
        raise Exception("Operation Cancelled")

def process_video(file):
    global cancel_requested, current_segments
    cancel_requested = False
    current_segments = []
    temp_audio = None

    safe_gui(button.configure, state="disabled", text="Processing...")
    safe_gui(cancel_button.configure, state="normal")
    safe_gui(save_button.configure, state="disabled")

    try:
        if not is_ffmpeg_available():
            safe_gui(status.configure, text="❌ FFmpeg not found")
            safe_gui(textbox.delete, "1.0", "end")
            safe_gui(
                textbox.insert,
                "end",
                "Error: FFmpeg executable is not found on your system PATH.\nPlease install FFmpeg to continue."
            )
            return

        perf_config = detect_optimal_hardware_config()
        lang_name, lang_code = get_selected_language_name_and_code()

        safe_gui(status.configure, text="⏳ Extracting audio...")
        temp_audio = extract_audio(file)
        check_cancel()

        safe_gui(status.configure, text=f"⏳ Splitting audio for {perf_config['model_name']} engine...")
        chunks = split_audio_into_chunks(temp_audio, perf_config["chunk_duration"])
        check_cancel()

        chunk_results = []
        total_chunks = len(chunks)
        start_time = time.time()

        for idx, chunk in enumerate(chunks, start=1):
            check_cancel()

            elapsed = time.time() - start_time
            eta_str = calculate_eta(idx - 1, total_chunks, elapsed)

            safe_gui(
                task_metrics_lbl.configure,
                text=f"Chunk: {idx}/{total_chunks}  |  ETA: {eta_str}  |  Model: {perf_config['model_name']}  |  Lang: {lang_name}"
            )
            safe_gui(
                status.configure,
                text=f"🎤 Transcribing chunk {idx}/{total_chunks} ({perf_config['model_name']} | {perf_config['device']})..."
            )

            chunk_segments = transcribe_video_segments(
                audio_path=chunk["chunk_path"],
                model_name=perf_config["model_name"],
                device=perf_config["device"],
                compute_type=perf_config["compute_type"],
                language=lang_code
            )

            chunk_results.append({
                "start_offset": chunk["start_offset"],
                "segments": chunk_segments
            })

            if chunk.get("is_temp"):
                cleanup_file(chunk["chunk_path"])

        check_cancel()
        merged_segments = merge_chunk_segments(chunk_results)
        transcript_text = "\n".join(s["text"] for s in merged_segments)

        if not is_valid_transcript(transcript_text):
            safe_gui(status.configure, text="❌ No meaningful speech detected.")
            safe_gui(textbox.delete, "1.0", "end")
            safe_gui(textbox.insert, "end", get_validation_error_message())
            return

        current_segments = merged_segments
        safe_gui(textbox.delete, "1.0", "end")
        safe_gui(textbox.insert, "end", transcript_text)
        safe_gui(save_button.configure, state="normal")
        safe_gui(status.configure, text=f"✅ Completed! ({perf_config['model_name']} model)")
        safe_gui(
            task_metrics_lbl.configure,
            text=f"Chunk: {total_chunks}/{total_chunks}  |  ETA: 00m 00s  |  Model: {perf_config['model_name']}  |  Lang: {lang_name}"
        )

    except Exception as e:
        if str(e) != "Operation Cancelled":
            safe_gui(status.configure, text="❌ Error")
            safe_gui(textbox.delete, "1.0", "end")
            safe_gui(textbox.insert, "end", str(e))
    finally:
        if temp_audio:
            cleanup_file(temp_audio)
        safe_gui(button.configure, state="normal", text="Select Video")
        safe_gui(cancel_button.configure, state="disabled")

def open_video():
    file = filedialog.askopenfilename(filetypes=SUPPORTED_VIDEO_TYPES)
    if not file:
        return
    threading.Thread(target=process_video, args=(file,), daemon=True).start()

def save_transcript():
    export_data = current_segments if current_segments else textbox.get("1.0", "end").strip()
    if not export_data:
        return

    file = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=SUPPORTED_EXPORT_FORMATS
    )
    if file:
        try:
            save_transcript_to_file(export_data, file)
            messagebox.showinfo("Success", "Transcript saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transcript: {str(e)}")

button = ctk.CTkButton(app, text="Select Video", command=open_video)
button.pack()

save_button = ctk.CTkButton(app, text="Download Transcript", command=save_transcript, state="disabled")
save_button.pack(pady=5)

cancel_button = ctk.CTkButton(app, text="Cancel", command=cancel_process, state="disabled")
cancel_button.pack(pady=5)

if __name__ == "__main__":
    app.mainloop()