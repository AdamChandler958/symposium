from fastapi import FastAPI
import uvicorn
from pytubefix import YouTube
import ffmpeg
import io

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Processing service is running"}

#TODO: This assumes it is a youtube mp3 url. This will be updated later to use metadata passed by
# the fetching service to determine how to retrieve the data.
@app.post("/retrieve_audio_stream/")
def retrieve_audio(url: str):
    yt_stream = YouTube(url)
    audio_stream = yt_stream.streams.filter(only_audio=True).first()
    audio_url = audio_stream.url


    stdout_data, stderr_data = (
    ffmpeg
    .input(audio_url)
    .output('pipe:1', format='mp3', acodec='libmp3lame')
    .run(capture_stdout=True, capture_stderr=True)
    )

    output_buffer = io.BytesIO(stdout_data)
    output_buffer.seek(0)

    return output_buffer

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3020, reload=True)