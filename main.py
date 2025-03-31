import edge_tts
import os
import asyncio
import uuid
from pathlib import Path
from fastapi.responses import FileResponse
from pydub import AudioSegment

# Temporary directory for audio outputs
OUTPUT_DIR = Path("temp")
OUTPUT_DIR.mkdir(exist_ok=True)

async def generate_audio(text: str, voice: str, output_file: Path):
    communicate = edge_tts.Communicate(text, voice)
    print(f"Generating audio for: {text[:50]}...")
    await communicate.save(str(output_file))
    await asyncio.sleep(0.1)  # Ensure file write completes
    if not output_file.exists() or output_file.stat().st_size == 0:
        raise Exception(f"Audio file not generated or empty: {output_file}")
    print(f"Generated: {output_file}, size: {output_file.stat().st_size} bytes")
    return output_file

async def handler(method: str = "GET", data: dict = None):
    """
    Edge TTS plugin: Converts text to speech using edge-tts with Hindi voice.
    Handles both GET (URL params) and POST (JSON payload), supports long text.
    """
    # Extract text based on method
    text = None
    if method in ("GET", "POST") and data and "text" in data:
        text = data["text"]

    if not text:
        return {
            "message": "No text provided",
            "plugin": "edgetts",
            "method": method,
            "info": "Provide 'text' in GET params or POST data"
        }

    try:
        voice = "hi-IN-NeerjaNeural"
        # Generate a unique file name per request
        unique_id = uuid.uuid4().hex
        audio_file = OUTPUT_DIR / f"output_{unique_id}.mp3"
        
        # Split text into chunks if it exceeds a certain length
        max_chunk_length = 1000  # Adjust based on TTS limitations
        if len(text) > max_chunk_length:
            segments = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            segment_files = []
            for i, segment in enumerate(segments):
                segment_file = OUTPUT_DIR / f"segment_{unique_id}_{i}.mp3"
                await generate_audio(segment, voice, segment_file)
                segment_files.append(segment_file)

            # Concatenate all segment files into one
            combined = AudioSegment.empty()
            for seg_file in segment_files:
                audio = AudioSegment.from_mp3(seg_file)
                combined += audio
            combined.export(audio_file, format="mp3")
            print(f"Combined audio: {audio_file}, size: {audio_file.stat().st_size} bytes")
        else:
            await generate_audio(text, voice, audio_file)

        if not audio_file.exists() or audio_file.stat().st_size == 0:
            raise Exception(f"Final audio file not generated or empty: {audio_file}")

        # Return file as response
        response = FileResponse(
            path=str(audio_file),
            filename="output.mp3",
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=output.mp3"}
        )
        return response

    except Exception as e:
        return {
            "message": "TTS generation failed",
            "plugin": "edgetts",
            "method": method,
            "error": str(e)
        }
    finally:
        await asyncio.sleep(0.5)  # Ensure response is sent
        # Cleanup all temp files
        for temp_file in OUTPUT_DIR.glob(f"*{unique_id}*.mp3"):
            if temp_file.exists():
                print(f"Cleaning up: {temp_file}")
                os.remove(temp_file)
