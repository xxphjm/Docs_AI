import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { askQuestion, healthCheck, uploadPdf } from './api/client'
import type { ChatMessage, SourceCitation } from './types'

const samplePrompts = [
  '這份文件的主要技術架構是什麼？',
  '請整理文件裡提到的監控工具。',
  '如果我要回滾，文件怎麼建議？',
]

function createSessionId() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `session-${Date.now()}`
}

function sourceTitle(source: SourceCitation) {
  return source.page ? `${source.source} · 第 ${source.page} 頁` : source.source
}

export default function App() {
  const [sessionId] = useState(() => createSessionId())
  const [collectionName, setCollectionName] = useState('docs_ai')
  const [question, setQuestion] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '把 PDF 上傳到左側，然後開始問我文件內容。',
    },
  ])
  const [isUploading, setIsUploading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [serviceStatus, setServiceStatus] = useState('checking')
  const [serviceDetail, setServiceDetail] = useState('Connecting to backend...')
  const [lastUpload, setLastUpload] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    let mounted = true

    healthCheck()
      .then((result) => {
        if (!mounted) return
        setServiceStatus(result.status)
        setServiceDetail(result.service)
      })
      .catch(() => {
        if (!mounted) return
        setServiceStatus('offline')
        setServiceDetail('Backend unavailable')
      })

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isSending])

  async function handleUpload() {
    if (!selectedFile) return

    setIsUploading(true)
    try {
      const response = await uploadPdf(selectedFile, collectionName)
      setLastUpload(`${response.filename} · ${response.status}`)
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-upload`,
          role: 'assistant',
          content: `已建立知識庫：${response.filename}`,
        },
      ])
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Upload failed'
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-upload-error`,
          role: 'assistant',
          content: `上傳失敗：${detail}`,
        },
      ])
    } finally {
      setIsUploading(false)
    }
  }

  async function handleSend(nextQuestion?: string) {
    const finalQuestion = (nextQuestion ?? question).trim()
    if (!finalQuestion || isSending) return

    setQuestion('')
    setIsSending(true)
    setMessages((current) => [
      ...current,
      {
        id: `${Date.now()}-user`,
        role: 'user',
        content: finalQuestion,
      },
    ])

    try {
      const response = await askQuestion(finalQuestion, sessionId, collectionName)
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
        },
      ])
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Request failed'
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-error`,
          role: 'assistant',
          content: `回覆失敗：${detail}`,
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <main className="shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <section className="workspace">
        <aside className="rail">
          <div className="panel panel-upload">
            <div className="panel-head">
              <div>
                <p className="panel-kicker">Knowledge Base</p>
                <h2>Upload documents</h2>
              </div>
              <span className="badge">PDF</span>
            </div>

            <label className="field">
              <span>Collection name</span>
              <input
                value={collectionName}
                onChange={(event) => setCollectionName(event.target.value)}
                placeholder="docs_ai"
              />
            </label>

            <label className="dropzone">
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
              <span className="dropzone-title">
                {selectedFile ? selectedFile.name : 'Drop a PDF here or click to choose'}
              </span>
              <span className="dropzone-subtitle">Files are ingested into Chroma after upload.</span>
            </label>

            <button className="primary-button" type="button" onClick={handleUpload} disabled={!selectedFile || isUploading}>
              {isUploading ? 'Ingesting…' : 'Build knowledge base'}
            </button>

            <div className="upload-meta">
              <span>Last upload</span>
              <strong>{lastUpload ?? 'None yet'}</strong>
            </div>
          </div>

        </aside>

        <section className="main-panel">
          <div className="panel panel-chat">
            <div className="panel-head chat-head">
              <div>
                <p className="panel-kicker">Conversation</p>
                <h2>Ask the document</h2>
              </div>
              <div className="status-pill">
                <span className={`dot ${serviceStatus}`} />
                {serviceStatus}
              </div>
            </div>

            <div className="chat-stream">
              {messages.map((message) => (
                <article key={message.id} className={`message message-${message.role}`}>
                  <div className="message-meta">{message.role === 'user' ? 'You' : 'TechDoc AI'}</div>
                  {message.role === 'assistant' ? (
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                  {message.sources && message.sources.length > 0 && (
                    <div className="citation-row">
                      <span className="sources-label">引用</span>
                      {message.sources.map((source, index) => (
                        <div key={`${source.source}-${index}`} className="citation-wrap">
                          <button
                            type="button"
                            className="citation-chip"
                            title={sourceTitle(source)}
                            aria-label={sourceTitle(source)}
                          >
                            {index + 1}
                          </button>
                          <div className="citation-popover">
                            <strong>{source.source}</strong>
                            <span>{source.page ? `第 ${source.page} 頁` : '未標示頁碼'}</span>
                            {source.snippet && <p>{source.snippet}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              ))}
              {isSending && (
                <article className="message message-assistant message-pending" aria-live="polite">
                  <div className="message-meta">TechDoc AI</div>
                  <div className="typing-indicator" aria-label="Waiting for reply">
                    <span />
                    <span />
                    <span />
                  </div>
                  <p className="pending-copy">正在整理文件內容，請稍候。</p>
                </article>
              )}
              <div ref={chatEndRef} />
            </div>

            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault()
                void handleSend()
              }}
            >
              <div className="composer-suggestions" aria-label="Suggested questions">
                {samplePrompts.map((prompt) => (
                  <button key={prompt} type="button" className="prompt-chip prompt-chip-inline" onClick={() => handleSend(prompt)} disabled={isSending}>
                    {prompt}
                  </button>
                ))}
              </div>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a question about the uploaded PDF..."
                rows={3}
              />
              <div className="composer-actions">
                <p className="composer-hint">Multi-turn memory is on for this session.</p>
                <button className="primary-button" type="submit" disabled={isSending}>
                  {isSending ? 'Thinking…' : 'Send question'}
                </button>
              </div>
            </form>
          </div>
        </section>
      </section>
    </main>
  )
}
