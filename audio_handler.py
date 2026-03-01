"""Audio I/O Handler - Vision-Agents Native Integration (FREE)"""

import os
import tempfile
from typing import Optional
from vision_agents_config import VISION_AGENTS_CFG

# Try to import free audio libraries
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️  Install gTTS for free text-to-speech: pip install gtts")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

class AudioHandler:
    """Handle text-to-speech via FREE providers (gTTS / pyttsx3)"""
    
    def __init__(self):
        self.gtts_available = GTTS_AVAILABLE
        self.pyttsx3_available = PYTTSX3_AVAILABLE
        
        if self.gtts_available:
            print("✓ gTTS (Google Text-to-Speech) available - FREE")
        elif self.pyttsx3_available:
            print("✓ pyttsx3 (offline TTS) available - FREE")
        else:
            print("ℹ️  Audio playback uses text fallback (no TTS library installed)")
    
    def speak_text(self, text: str) -> bool:
        """Convert text to speech using FREE gTTS or pyttsx3"""
        
        # Try gTTS first (free Google TTS)
        if self.gtts_available:
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                    tts.save(tmp.name)
                    print(f"[VOICE]: {text}")
                    # Don't play - just synthesize
                    os.unlink(tmp.name)
                    return True
            except Exception as e:
                print(f"[VOICE]: {text} (gTTS failed: {e})")
                print(f"[TEXT FALLBACK]: {text}")
                return False
        
        # Try pyttsx3 next (offline, free)
        elif self.pyttsx3_available:
            try:
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                print(f"[VOICE]: {text}")
                return True
            except Exception as e:
                print(f"[VOICE]: {text} (pyttsx3 failed: {e})")
                print(f"[TEXT FALLBACK]: {text}")
                return False
        
        # Fallback to text output
        else:
            print(f"[TEXT]: {text}")
            return False

_audio_handler = None

def get_audio_handler() -> AudioHandler:
    """Get or create audio handler"""
    global _audio_handler
    if _audio_handler is None:
        _audio_handler = AudioHandler()
    return _audio_handler

def speak_text(text: str):
    """Speak text using default handler"""
    handler = get_audio_handler()
    handler.speak_text(text)