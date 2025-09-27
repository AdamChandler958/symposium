from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from pytubefix import YouTube
import ffmpeg
import logging
from src.logging import setup_logger

app = FastAPI()
setup_logger()
logger = logging.getLogger("processing-service")

@app.get("/")
def read_root():
    return {"message": "Processing service is running"}

#TODO: This assumes it is a youtube mp3 url. This will be updated later to use metadata passed by
# the fetching service to determine how to retrieve the data.
@app.get("/retrieve-audio_stream") 
def retrieve_audio_stream(url: str):
    logger.info(f"Received request to process URL to audio for URL: {url}")
    try:
        yt_stream = YouTube(url)
        audio_url = yt_stream.streams.filter(only_audio=True).first().url

        process = (
            ffmpeg
            .input(audio_url)
            .output('pipe:1', format='mp3', acodec='libmp3lame')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )


        def audio_stream_generator():
            while True:
                chunk = process.stdout.read(64 * 1024) 
                if not chunk:
                    break
                yield chunk
            
            process.wait()

        return StreamingResponse(
            audio_stream_generator(),
            media_type="audio/mp3",
            headers={
                "Content-Type": "audio/mp3", 
                "Content-Disposition": "attachment; filename=audio.mp3"
            }
        )

    except Exception as e:
        logger.error(f"Error occured while processing audio with error: {e}")
        raise e

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3020, reload=True)