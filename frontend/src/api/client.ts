import type { ChatResponse, UploadResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function toJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function uploadPdf(file: File, collectionName: string): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('collection_name', collectionName)

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })

  return toJson<UploadResponse>(response)
}

export async function askQuestion(
  question: string,
  sessionId: string,
  collectionName: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      collection_name: collectionName,
    }),
  })

  return toJson<ChatResponse>(response)
}

export async function healthCheck(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE}/health`)
  return toJson<{ status: string; service: string }>(response)
}

