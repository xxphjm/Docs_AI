from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langsmith import Client as LangSmithClient

from backend.app.db import ChromaDB
from backend.app.util.setting import Settings


settings = Settings()


class Agent:
    def __init__(self, collection_name: str = "docs_ai"):
        self.client = ChatNVIDIA(
            model=settings.LLM_MODEL,
            api_key=settings.NVIDIA_API_KEY,
            temperature=0.2,
            top_p=0.95,
            max_completion_tokens=2048,
        )
        self.db = ChromaDB(collection_name=collection_name)
        self.retriever = self.db.as_retriever(n_results=5)
        self.prompt = LangSmithClient(api_key=settings.LANGSMITH_API_KEY).pull_prompt(
            settings.PROMPT_NAME, include_model=True
        )
        self.qa_chain = create_stuff_documents_chain(self.client, self.prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.qa_chain)
        self.history_store = {}
        self.collection_name = collection_name
        self.rag_chain_with_history = RunnableWithMessageHistory(
            self.rag_chain,
            self.get_session_history,
            input_messages_key="input",
            output_messages_key="answer",
            history_messages_key="chat_history",
        )

    def ask(self, question: str, session_id: str = "default"):
        result = self.rag_chain_with_history.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )
        answer = result["answer"]
        sources = []

        for doc in result.get("context", []):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", None)
            sources.append(
                {
                    "source": source,
                    "page": page + 1 if isinstance(page, int) else None,
                    "snippet": doc.page_content[:220].strip(),
                }
            )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    def get_session_history(self, session_id: str):
        if session_id not in self.history_store:
            self.history_store[session_id] = InMemoryChatMessageHistory()
        return self.history_store[session_id]


if __name__ == "__main__":
    agent = Agent()
    session_id = "demo"
    question = "請問文件中有提到哪些技術嗎？"
    result = agent.ask(question, session_id=session_id)
    print("問題：", result["question"])
    print("回答：", result["answer"])
    for src in result["sources"]:
        page = f" 第{src['page']}頁" if src.get("page") else ""
        print(f"來源：{src['source']}{page}")
