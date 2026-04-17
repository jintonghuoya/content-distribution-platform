export interface Topic {
  id: number
  title: string
  source: string
  source_id: string
  source_url: string
  rank: number | null
  heat_value: number | null
  category: string | null
  priority: number | null
  status: 'pending' | 'filtered' | 'rejected' | 'generating' | 'published'
  collected_at: string
  created_at: string
}

export interface TopicListResponse {
  total: number
  items: Topic[]
}

export interface FilterRule {
  id: number
  name: string
  rule_type: 'keyword_blacklist' | 'heat_threshold' | 'source_weight'
  config: Record<string, any>
  enabled: boolean
  run_order: number
  created_at: string
}

export interface GeneratedContent {
  id: number
  topic_id: number
  content_type: string
  title: string
  body: string
  prompt_name: string
  llm_model: string
  status: string
  metadata: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface GeneratedContentListResponse {
  total: number
  items: GeneratedContent[]
}

export interface DistributionRecord {
  id: number
  content_id: number
  platform: string
  success: boolean
  mode: string
  platform_content_id: string
  platform_url: string
  package_data: Record<string, any> | null
  error_message: string
  published_at: string
  created_at: string
}

export interface RevenueRecord {
  id: number
  platform: string
  content_id: number
  date: string
  views: number
  likes: number
  comments: number
  shares: number
  revenue_amount: number
  currency: string
  recorded_at: string
  created_at: string
}

export interface SourceInfo {
  source: string
  name: string
  enabled: boolean
  interval_seconds: number
}

export interface PlatformConfig {
  id: number
  name: string
  display_name: string
  api_key?: string
  cookie?: string
  app_secret?: string
  app_id?: string
  extra?: Record<string, string>
  created_at: string
  updated_at: string
}

export interface TriggerResponse {
  total: number
  [key: string]: any
  message?: string
}

export type StatusType = 'pending' | 'filtered' | 'rejected' | 'generating' | 'published' | 'draft'
