import edge_tts
import os
from pathlib import Path
from fastapi.responses import FileResponse

# Temporary file path for audio output
OUTPUT_DIR = Path("temp")
OUTPUT_DIR.mkdir(exist_ok=True)
AUDIO_FILE = OUTPUT_DIR / "output.mp3"

async def handler(method: str = "GET", data: dict = None):
    """
    Edge TTS plugin: Converts text to speech using edge-tts with Hindi voice.
    - GET: Uses 'text' from URL params (passed via data).
    - POST: Uses 'text' from JSON payload (passed via data).
    Returns audio file or error message.
    """
    # Extract text based on method
    text = None
    if method == "GET" and data and "text" in data:
        text = data["text"]
    elif method == "POST" and data and "text" in data:
        text = data["text"]

    if not text:
        return {
            "message": "No text provided",
            "plugin": "edgetts",
            "method": method,
            "info": "Provide 'text' in GET params or POST data"
        }

    try:
        # Use edge-tts with Hindi voice (Neerja or default Hindi)
        voice = "hi-IN-NeerjaNeural"  # Neerja voice, Azure-based
        communicate = edge_tts.Communicate(text, voice)
        
        # Save audio to file asynchronously
        await communicate.save(str(AUDIO_FILE))

        if not AUDIO_FILE.exists():
            raise Exception("Failed to generate audio file")

        # Return file as response
        return FileResponse(
            path=str(AUDIO_FILE),
            filename="output.mp3",
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=output.mp3"}
        )

    except Exception as e:
        return {
            "message": "TTS generation failed",
            "plugin": "edgetts",
            "method": method,
            "error": str(e)
        }
    finally:
        # Cleanup
        if AUDIO_FILE.exists():
            os.remove(AUDIO_FILE)
