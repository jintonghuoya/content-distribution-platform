import request from './request'
import type { TopicListResponse, Topic } from '@/types'

export function getTopics(params: {
  source?: string
  status?: string
  page?: number
  size?: number
}) {
  return request.get<TopicListResponse>('/topics', { params })
}

export function getTopic(id: number) {
  return request.get<Topic>(`/topics/${id}`)
}
