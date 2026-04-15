import request from './request'
import type { SourceInfo } from '@/types'

export function getSources() {
  return request.get<SourceInfo[]>('/sources')
}

export function toggleSource(sourceName: string, enabled: boolean) {
  return request.put(`/sources/${sourceName}`, { enabled })
}

export function collectTopics() {
  return request.post('/topics/collect')
}
