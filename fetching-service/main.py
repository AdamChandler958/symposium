from fastapi import FastAPI
import uvicorn
from src.logging import setup_logger
import logging
from src.pydantic_models import MetaDataResponse
from src.providers import SupportedProviders

setup_logger()
logger = logging.getLogger("fetching-service")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Fetching service is running"}

@app.get("/stream_metadata")
def search_metadata(url: str) -> MetaDataResponse:
    response_object = MetaDataResponse()
    if "youtube.com" in url or "youtu.be" in url:
        response_object.provider = SupportedProviders.YT
    else:
        return
    return

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)