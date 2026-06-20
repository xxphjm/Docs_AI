from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str = Field(default="default")
    collection_name: str = Field(default="docs_ai")


class SourceCitation(BaseModel):
    source: str
    page: int | None = None
    snippet: str | None = None


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceCitation] = Field(default_factory=list)
