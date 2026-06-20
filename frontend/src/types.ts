export type SourceCitation = {
  source: string
  page?: number | null
  snippet?: string | null
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceCitation[]
  isPending?: boolean
}

export type UploadResponse = {
  filename: string
  collection_name: string
  status: string
}

export type ChatResponse = {
  question: string
  answer: string
  sources: SourceCitation[]
}
