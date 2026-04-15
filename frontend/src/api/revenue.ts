import request from './request'
import type { RevenueRecord } from '@/types'

export function getRevenueRecords(params: {
  platform?: string
  content_id?: number
  page?: number
  size?: number
}) {
  return request.get<RevenueRecord[]>('/revenue/records', { params })
}

export function getRevenueSummary(platform?: string, days: number = 30) {
  return request.get('/revenue/summary', { params: { platform, days } })
}

export function triggerRevenueCollect() {
  return request.post('/revenue/collect')
}
