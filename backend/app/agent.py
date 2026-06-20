from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from backend.app.db import ChromaDB
from backend.app.util.setting import Settings


settings = Settings()


class Agent:
    def __init__(self, collection_name: str = "docs_ai"):
        self.client = ChatNVIDIA(
            model="google/gemma-4-31b-it",
            api_key=settings.NVIDIA_API_KEY,
            temperature=0.2,
            top_p=0.95,
            max_completion_tokens=2048,
        )
        self.db = ChromaDB(collection_name=collection_name)
        self.retriever = self.db.as_retriever(n_results=5)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    你是一位文件分析與 AI 助理。

                    請優先根據提供的文件內容回答問題。

                    當使用者要求摘要、分析、評論、建議、改寫、
                    優化或延伸討論時，可以根據文件內容進行合理推論。

                    不要捏造文件不存在的事實。

                    如果文件中完全沒有相關資訊，
                    請明確告知使用者。

                    文件內容：
                    {context}
                    """,
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
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
    if result["sources"]:
        print("來源：", "、".join(result["sources"]))
