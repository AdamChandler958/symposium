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
@app.get("/retrieve-audio-stream") 
def retrieve_audio_stream(url: str):
    logger.info(f"Received request to process URL to audio for URL: {url}")
    try:
        yt_stream = YouTube(url)
        audio_url = yt_stream.streams.filter(only_audio=True, use_oauth=False, allow_oauth_cache=False, use_po_token=True).first().url

        process = (
            ffmpeg
            .input(audio_url)
            .output('pipe:1', format='opus', acodec='libopus')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )


        def audio_stream_generator():
            try:
                while True:
                    chunk = process.stdout.read(64 * 1024) 
                    
                    if chunk:
                        yield chunk
                    else:
                        if process.poll() is not None:

                            logger.info("FFmpeg process finished and pipe exhausted. Breaking generator loop.")
                            break 
                        else:
                            continue 

            except Exception as e:
                logger.error(f"Error during audio streaming: {e}")
            finally:
                return_code = process.wait() 
                remaining_chunk = process.stdout.read()
                if remaining_chunk:
                    yield remaining_chunk
                    
                if return_code != 0:
                    stderr_output = process.stderr.read().decode()
                    logger.error(f"FFmpeg process exited with error code {return_code}. Stderr: {stderr_output}")
                else:
                    logger.info("FFmpeg process completed successfully.")
                

        return StreamingResponse(
            audio_stream_generator(),
            media_type="audio/opus",
            headers={
                "Content-Type": "audio/opus", 
                "Content-Disposition": "attachment; filename=audio.opus",
                "Connection": "close"
            }
        )

    except Exception as e:
        logger.error(f"Error occured while processing audio with error: {e}")
        raise e

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3020, reload=True)