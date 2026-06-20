from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filename: str
    collection_name: str
    status: str = "ingested"


class HealthResponse(BaseModel):
    status: str
    service: str

