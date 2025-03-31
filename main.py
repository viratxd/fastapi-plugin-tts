import edge_tts
import os
import asyncio
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
        # Use edge-tts with Hindi voice (Neerja)
        voice = "hi-IN-NeerjaNeural"
        communicate = edge_tts.Communicate(text, voice)
        
        # Save audio to file asynchronously and ensure completion
        print(f"Generating audio for text: {text}")
        await communicate.save(str(AUDIO_FILE))
        
        # Wait briefly to ensure file is fully written
        await asyncio.sleep(0.1)  # Small delay to avoid race condition
        
        if not AUDIO_FILE.exists() or AUDIO_FILE.stat().st_size == 0:
            raise Exception(f"Audio file not generated or empty: {AUDIO_FILE}")

        print(f"Audio file generated: {AUDIO_FILE}, size: {AUDIO_FILE.stat().st_size} bytes")

        # Return file as response
        response = FileResponse(
            path=str(AUDIO_FILE),
            filename="output.mp3",
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=output.mp3"}
        )

        # Cleanup after response is prepared (not before)
        return response

    except Exception as e:
        return {
            "message": "TTS generation failed",
            "plugin": "edgetts",
            "method": method,
            "error": str(e)
        }
    finally:
        # Delay cleanup to ensure response is sent
        await asyncio.sleep(0.5)  # Give time for response to be sent
        if AUDIO_FILE.exists():
            print(f"Cleaning up: {AUDIO_FILE}")
            os.remove(AUDIO_FILE)
