import edge_tts
import os
import asyncio
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydub import AudioSegment

app = FastAPI()

# Define base directory
BASE_DIR = Path(__file__).resolve().parent  # Gets the script's parent directory
OUTPUT_DIR = BASE_DIR / "temp"
OUTPUT_DIR.mkdir(exist_ok=True)

async def generate_audio(text: str, voice: str, output_file: Path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_file))
    await asyncio.sleep(0.1)  # Ensure file write completes
    if not output_file.exists() or output_file.stat().st_size == 0:
        raise Exception(f"Audio file not generated or empty: {output_file}")
    return output_file

@app.post("/generate-audio")
async def generate_tts(data: dict):
    if "text" not in data:
        raise HTTPException(status_code=400, detail="No text provided")
    
    text = data["text"]
    voice = "hi-IN-SwaraNeural"
    unique_id = uuid.uuid4().hex
    audio_file = OUTPUT_DIR / f"output_{unique_id}.mp3"
    
    try:
        max_chunk_length = 1000
        if len(text) > max_chunk_length:
            segments = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            segment_files = []

            for i, segment in enumerate(segments):
                segment_file = OUTPUT_DIR / f"segment_{unique_id}_{i}.mp3"
                await generate_audio(segment, voice, segment_file)
                segment_files.append(segment_file)

            # Merge audio segments
            combined = AudioSegment.empty()
            for seg_file in segment_files:
                audio = AudioSegment.from_mp3(seg_file)
                combined += audio
            combined.export(audio_file, format="mp3")
        else:
            await generate_audio(text, voice, audio_file)

        if not audio_file.exists() or audio_file.stat().st_size == 0:
            raise Exception("Final audio file not generated or empty")
        
        return FileResponse(
            path=audio_file,
            filename="output.mp3",
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=output.mp3"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
