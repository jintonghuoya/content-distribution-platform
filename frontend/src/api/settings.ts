import request from './request'
import type { PlatformConfig } from '@/types'

export function getPlatformConfigs() {
  return request.get<PlatformConfig[]>('/settings/platforms')
}

export function updatePlatformConfig(name: string, data: Partial<PlatformConfig>) {
  return request.put(`/settings/platforms/${name}`, data)
}
