from fastapi import FastAPI
import uvicorn
from src.logging import setup_logger
import logging
from src.pydantic_models import MetaDataResponse
from src.providers import SupportedProviders
from src.query_engine import fetch_youtube_by_query, get_video_details_from_url

setup_logger()
logger = logging.getLogger("fetching-service")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Fetching service is running"}

@app.get("/stream_metadata")
def search_metadata(url_query: str) -> MetaDataResponse | None:
    if "youtube.com" in url_query or "youtu.be" in url_query:
        logger.info("Youtube url detected")
        
        metadata = get_video_details_from_url(url_query)
        if metadata:
            response_object = MetaDataResponse(provider=SupportedProviders.YT, 
                                                url=metadata.get("url"), 
                                                title=metadata.get("title"),
                                                duration=metadata.get("duration"))
            return response_object
    else:
        logger.info("Non-standard provider detected")
        search_results = fetch_youtube_by_query(url_query)
        if search_results:
            response_object = MetaDataResponse(provider=SupportedProviders.YT, 
                                                url=search_results.get("url"), 
                                                title=search_results.get("title"),
                                                duration=search_results.get("duration"))
            return response_object
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)