import os

# Application Configuration Constants
DEFAULT_MODEL = "base"
DEFAULT_COMPUTE_TYPE = "int8"
DEFAULT_DEVICE = "cpu"

OUTPUT_DIR = os.path.abspath("output")
UPLOADS_DIR = os.path.abspath("uploads")

SUPPORTED_VIDEO_TYPES = [("Video Files", "*.mp4 *.mov *.avi *.mkv *.webm *.flv")]
SUPPORTED_EXPORT_FORMATS = [
    ("Text File", "*.txt"),
    ("SubRip Subtitle", "*.srt"),
    ("WebVTT Subtitle", "*.vtt"),
]

# Language Selector Configuration
PRIMARY_LANGUAGES = [
    ("Auto Detect", None),
    ("English", "en"),
    ("Hindi", "hi"),
    ("Other...", "other"),
]

ALL_WHISPER_LANGUAGES = [
    ("Arabic", "ar"),
    ("Bengali", "bn"),
    ("Chinese", "zh"),
    ("Dutch", "nl"),
    ("English", "en"),
    ("French", "fr"),
    ("German", "de"),
    ("Gujarati", "gu"),
    ("Hindi", "hi"),
    ("Italian", "it"),
    ("Japanese", "ja"),
    ("Kannada", "kn"),
    ("Korean", "ko"),
    ("Malayalam", "ml"),
    ("Marathi", "mr"),
    ("Nepali", "ne"),
    ("Polish", "pl"),
    ("Portuguese", "pt"),
    ("Punjabi", "pa"),
    ("Russian", "ru"),
    ("Spanish", "es"),
    ("Tamil", "ta"),
    ("Telugu", "te"),
    ("Turkish", "tr"),
    ("Urdu", "ur"),
    ("Vietnamese", "vi"),
]
