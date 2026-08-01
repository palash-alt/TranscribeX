import os

# Application Configuration Constants
DEFAULT_MODEL = "base"
DEFAULT_COMPUTE_TYPE = "int8"
DEFAULT_DEVICE = "cpu"

OUTPUT_DIR = os.path.abspath("output")
UPLOADS_DIR = os.path.abspath("uploads")

SUPPORTED_VIDEO_TYPES = [("Video Files", "*.mp4 *.mov *.avi *.mkv *.webm *.flv")]
SUPPORTED_EXPORT_FORMATS = [("Text File", "*.txt")]
