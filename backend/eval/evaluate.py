"""
LangSmith Evaluation Script for TechDoc AI Assistant

使用方式：
  uv run python -m backend.eval.evaluate

第一次執行會自動建立 Dataset，之後每次執行都是一個新的 experiment。
每個 experiment 可以在 LangSmith 網站上互相比較。
"""

import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA  # noqa: F401 — used inside evaluators
from langsmith import Client
from langsmith.evaluation import evaluate

from backend.app.agent import Agent
from backend.app.util.setting import Settings

settings = Settings()

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY)
os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGSMITH_PROJECT)

DATASET_NAME = "docs_ai"
COLLECTION_NAME = "docs_ai"

# -----------------------------------------------------------------------
# 測試集
# 把你上傳的 PDF 裡，你已經知道答案的問題填進來。
# "output" 是你期望的「正確答案」，evaluator 會拿它來打分。
# -----------------------------------------------------------------------
EXAMPLES = [
    {
        "input": {"question": "請填入你的第一個測試問題"},
        "output": {"answer": "填入這題的預期正確答案"},
    },
    {
        "input": {"question": "請填入你的第二個測試問題"},
        "output": {"answer": "填入這題的預期正確答案"},
    },
    {
        "input": {"question": "請填入你的第三個測試問題"},
        "output": {"answer": "填入這題的預期正確答案"},
    },
]


# -----------------------------------------------------------------------
# Target function — LangSmith 把每筆 input 丟進來，取得 output 後打分
# -----------------------------------------------------------------------
_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent(collection_name=COLLECTION_NAME)
    return _agent


def target(inputs: dict) -> dict:
    question = inputs.get("question") or inputs.get("input") or next(iter(inputs.values()), "")
    result = get_agent().ask(str(question))
    return {"answer": result["answer"]}


# -----------------------------------------------------------------------
# Evaluators（langsmith 0.8.x 新版寫法）
#
# 每個 evaluator 接收 (run, example)，回傳 {"key": ..., "score": 0~1}
# run.outputs     → 你的 RAG 實際回答
# example.outputs → EXAMPLES 裡填的預期答案
# -----------------------------------------------------------------------
def _llm() -> ChatNVIDIA:
    return ChatNVIDIA(
        model="google/gemma-4-31b-it",
        api_key=settings.NVIDIA_API_KEY,
        temperature=0,
    )


def correctness_evaluator(run, example) -> dict:
    """用 LLM 對照 reference answer 評分回答正確性"""
    actual = (run.outputs or {}).get("answer", "")
    reference = (example.outputs or {}).get("answer", "")

    prompt = f"""你是一個嚴格的評分員。

參考答案：
{reference}

AI 回答：
{actual}

請判斷 AI 回答是否與參考答案語意一致、內容正確。
只回覆一個數字：1（正確）或 0（不正確）。不要回覆其他任何文字。"""

    response = _llm().invoke(prompt).content.strip()
    score = 1.0 if "1" in response else 0.0
    return {"key": "correctness", "score": score}


def groundedness_evaluator(run, _example) -> dict:
    """用 LLM 判斷回答有沒有脫離文件亂講（幻覺偵測）"""
    actual = (run.outputs or {}).get("answer", "")

    prompt = f"""你是一個評估 AI 回答品質的評分員。

AI 回答：
{actual}

請判斷這個回答是否符合以下標準：
- 回答有明確根據（引用文件、說明來源，或明確說「文件中無相關資訊」）
- 沒有捏造事實或無中生有

只回覆一個數字：1（有根據）或 0（有幻覺或無根據）。不要回覆其他任何文字。"""

    response = _llm().invoke(prompt).content.strip()
    score = 1.0 if "1" in response else 0.0
    return {"key": "groundedness", "score": score}


def length_evaluator(run, _example) -> dict:
    """簡單規則：回答是否在合理長度範圍內（不太短也不太長）"""
    actual = (run.outputs or {}).get("answer", "")
    char_count = len(actual)

    if char_count < 20:
        score = 0.0   # 太短，沒有實質回答
    elif char_count > 2000:
        score = 0.5   # 太長，可能冗余
    else:
        score = 1.0

    return {"key": "length_ok", "score": score}


# -----------------------------------------------------------------------
# 建立 Dataset（第一次執行才需要）
# -----------------------------------------------------------------------
def ensure_dataset(client: Client) -> str:
    existing = [ds.name for ds in client.list_datasets()]
    if DATASET_NAME in existing:
        print(f"Dataset '{DATASET_NAME}' 已存在，跳過建立。")
        return DATASET_NAME

    dataset = client.create_dataset(DATASET_NAME, description="TechDoc AI RAG 評測集")
    client.create_examples(
        inputs=[ex["input"] for ex in EXAMPLES],
        outputs=[ex["output"] for ex in EXAMPLES],
        dataset_id=dataset.id,
    )
    print(f"Dataset '{DATASET_NAME}' 建立完成，共 {len(EXAMPLES)} 筆。")
    return DATASET_NAME


# -----------------------------------------------------------------------
# 主程式
# -----------------------------------------------------------------------
if __name__ == "__main__":
    client = Client(api_key=settings.LANGSMITH_API_KEY)
    ensure_dataset(client)

    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            correctness_evaluator,
            groundedness_evaluator,
            length_evaluator,
        ],
        experiment_prefix="baseline",
        metadata={"model": "google/gemma-4-31b-it", "chunk_size": 1000},
    )

    print("\n=== 評測完成 ===")
    print(f"前往 LangSmith 查看結果：https://smith.langchain.com/")
    print(f"Project: {settings.LANGSMITH_PROJECT}  |  Dataset: {DATASET_NAME}")
