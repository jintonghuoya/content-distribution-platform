import request from './request'
import type { FilterRule } from '@/types'

export function getFilterRules() {
  return request.get<FilterRule[]>('/filters/rules')
}

export function createFilterRule(data: Omit<FilterRule, 'id' | 'created_at'>) {
  return request.post<FilterRule>('/filters/rules', data)
}

export function updateFilterRule(id: number, data: Omit<FilterRule, 'id' | 'created_at'>) {
  return request.put<FilterRule>(`/filters/rules/${id}`, data)
}

export function deleteFilterRule(id: number) {
  return request.delete(`/filters/rules/${id}`)
}

export function triggerFilterAll() {
  return request.post('/filters/trigger')
}

export function triggerFilterTopic(topicId: number) {
  return request.post(`/filters/trigger/${topicId}`)
}
