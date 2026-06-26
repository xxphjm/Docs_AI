from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from backend.app.util.setting import Settings

s = Settings()
client = Client(api_key=s.LANGSMITH_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ('system', '''你是一位文件分析與 AI 助理。

請優先根據提供的文件內容回答問題。

當使用者要求摘要、分析、評論、建議、改寫、
優化或延伸討論時，可以根據文件內容進行合理推論。

不要捏造文件不存在的事實。

如果文件中完全沒有相關資訊，
請明確告知使用者。

文件內容：
{context}'''),
    MessagesPlaceholder('chat_history'),
    ('human', '{input}'),
])

client.push_prompt('docs-ai-prompt', object=prompt)
print('上傳完成')
