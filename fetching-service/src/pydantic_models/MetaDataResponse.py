from pydantic import BaseModel

class MetaDataResponse(BaseModel):
    provider: str
    url: str
    title: str
    duration: str