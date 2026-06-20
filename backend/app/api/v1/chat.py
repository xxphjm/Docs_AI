from fastapi import APIRouter

from functools import lru_cache

from backend.app.agent import Agent
from backend.app.schemas.chat import ChatRequest, ChatResponse, SourceCitation


router = APIRouter(prefix="/chat", tags=["chat"])


@lru_cache(maxsize=8)
def get_agent(collection_name: str) -> Agent:
    return Agent(collection_name=collection_name)


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = get_agent(payload.collection_name).ask(payload.question, session_id=payload.session_id)
    sources = []
    for item in result.get("sources", []):
        if isinstance(item, dict):
            sources.append(SourceCitation(source=item.get("source", "unknown"), page=item.get("page")))
        else:
            sources.append(SourceCitation(source=str(item), page=None))
    return ChatResponse(question=result["question"], answer=result["answer"], sources=sources)
