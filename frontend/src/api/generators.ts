import request from './request'
import type { GeneratedContentListResponse, GeneratedContent } from '@/types'

export function listGenerators() {
  return request.get('/generators/')
}

export function triggerGenerateAll() {
  return request.post('/generators/trigger')
}

export function triggerGenerateTopic(topicId: number, generator?: string) {
  return request.post(`/generators/trigger/${topicId}`, null, {
    params: generator ? { generator } : {},
  })
}

export function getGeneratedContent(params: {
  topic_id?: number
  content_type?: string
  status?: string
  page?: number
  size?: number
}) {
  return request.get<GeneratedContentListResponse>('/generators/content', { params })
}

export function getGeneratedContentDetail(id: number) {
  return request.get<GeneratedContent>(`/generators/content/${id}`)
}

export function publishContent(id: number) {
  return request.put(`/generators/content/${id}/publish`)
}
