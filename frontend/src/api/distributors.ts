import request from './request'
import type { DistributionRecord } from '@/types'

export function listDistributors() {
  return request.get('/distributors/')
}

export function triggerDistributeAll() {
  return request.post('/distributors/trigger')
}

export function triggerDistributeContent(contentId: number, platform?: string) {
  return request.post(`/distributors/trigger/${contentId}`, null, {
    params: platform ? { platform } : {},
  })
}

export function getDistributionRecords(params: {
  content_id?: number
  platform?: string
  page?: number
  size?: number
}) {
  return request.get<DistributionRecord[]>('/distributors/records', { params })
}
