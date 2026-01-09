// API 响应通用结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 用户相关
export interface User {
  id: string
  email: string
  nickname: string
  avatar_url?: string
  role: 'user' | 'subscriber' | 'admin'
  subscription?: {
    plan: string
    expires_at?: string
  }
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  nickname: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  user: User
  tokens: TokenResponse
}

// 故事相关
export interface Category {
  id: string
  name: string
  name_en: string
  sort_order: number
  story_count?: number
}

export interface Story {
  id: string
  title: string
  title_en?: string
  category_id: string
  category_name?: string
  description?: string
  thumbnail_url: string
  video_url?: string
  audio_url?: string
  duration: number
  is_published: boolean
  view_count: number
  subtitles?: Subtitle[]
  created_at: string
  updated_at?: string
}

export interface Subtitle {
  start: number
  end: number
  text: string
}

// 声音档案
export interface VoiceProfile {
  id: string
  name: string
  voice_id: string
  reference_audio_url: string
  preview_audio_url: string
  created_at: string
}

// 头像档案
export interface AvatarProfile {
  id: string
  name: string
  image_url: string
  preview_video_url: string
  created_at: string
}

// 语音克隆任务
export interface VoiceCloneTask {
  task_id: string
  status: 'processing' | 'completed' | 'failed'
  progress: number
  audio_url?: string
  error?: string
}

// 数字人任务
export interface DigitalHumanTask {
  task_id: string
  status: 'detecting' | 'generating' | 'completed' | 'failed'
  progress: number
  video_url?: string
  error?: string
}

// 故事生成任务
export interface StoryGenerationJob {
  id: string
  user_id: string
  story_id: string
  voice_profile_id: string
  avatar_profile_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step: string
  final_video_url?: string
  error?: string
  created_at: string
  completed_at?: string
}

// 有声书故事
export interface AudiobookStory {
  id: string
  title: string
  title_en: string
  content: string
  language: 'en' | 'zh'
  category: string
  age_group: string
  estimated_duration: number
  thumbnail_url?: string
  background_music_url?: string
  is_published: boolean
}

// 有声书任务
export interface AudiobookJob {
  id: string
  story_id: string
  voice_profile_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step: string
  audio_url?: string
  duration?: number
  story_title: string
  voice_name: string
  created_at: string
  completed_at?: string
  error?: string
}

// 预设故事
export interface PresetStory {
  id: string
  title: string
  preview_text: string
  estimated_duration: number
}
