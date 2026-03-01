import os
from dotenv import load_dotenv

load_dotenv()

# Stream.io Configuration
STREAM_API_KEY = os.getenv("STREAM_API_KEY", "")
STREAM_API_SECRET = os.getenv("STREAM_API_SECRET", "")

# LLM Configuration (FREE TIER)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

VISION_AGENTS_CFG = {
    "stream": {
        "api_key": STREAM_API_KEY,
        "api_secret": STREAM_API_SECRET,
    },
    "gemini": {
        "api_key": GEMINI_API_KEY,
        "model": "gemini-2.5-flash-lite",  # Free tier model
        "fps": 5,  # Process 5 frames per second for efficiency
    },
    "tts": {
        "provider": "gtts",  # Free - Google Text-to-Speech
        "language": "en",
    },
    "stt": {
        "provider": "google",  # Free - Google Speech Recognition
    },
    # YOLO Configuration for detection
    "yolo": {
        "model": "yolov8m.pt",  # Medium model for balance
        "conf_threshold": 0.5,
        "device": "cpu",  # CPU by default (change to 'cuda' if GPU available)
    },
    # Driving-specific settings
    "driving": {
        "fps": 10,
        "max_distance_meters": 50,
        "min_object_confidence": 0.6,
        "voice_feedback_interval": 2.0,  # Seconds
    },
}