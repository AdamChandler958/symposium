from fastapi import FastAPI
import uvicorn
from src.logging import setup_logger
import logging

setup_logger()
logger = logging.getLogger("fetching-service")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Fetching service is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)