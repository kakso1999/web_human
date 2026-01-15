import { http } from './http'
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
  Category,
  Story,
  PaginatedResponse,
  VoiceProfile,
  AvatarProfile,
  VoiceCloneTask,
  DigitalHumanTask,
  StoryGenerationJob,
  AudiobookStory,
  AudiobookJob,
  PresetStory,
  Speaker,
  SpeakerConfig,
  CreateStoryJobRequest,
  SingleSpeakerAnalysis,
  DualSpeakerAnalysis,
  UserEbook
} from '@/types'

// ==================== 认证 API ====================
export const authApi = {
  login(data: LoginRequest) {
    return http.post<AuthResponse>('/auth/login', data)
  },

  register(data: RegisterRequest) {
    return http.post<AuthResponse>('/auth/register', data)
  },

  googleAuth(code: string) {
    return http.post<AuthResponse>('/auth/google', { code })
  },

  getGoogleAuthUrl() {
    return http.get<{ url: string }>('/auth/google/url')
  },

  refresh(refreshToken: string) {
    return http.post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken })
  },

  logout() {
    return http.post('/auth/logout')
  }
}

// ==================== 用户 API ====================
export const userApi = {
  getProfile() {
    return http.get<User>('/user/profile')
  },

  updateProfile(data: { nickname?: string }) {
    return http.put<User>('/user/profile', data)
  },

  uploadAvatar(file: File) {
    return http.upload<User>('/user/avatar', file, 'file')
  },

  changePassword(oldPassword: string, newPassword: string) {
    return http.post('/user/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
  }
}

// ==================== 故事 API ====================
export const storyApi = {
  getCategories() {
    return http.get<Category[]>('/stories/categories')
  },

  getStories(params?: {
    page?: number
    page_size?: number
    category_id?: string
    search?: string
  }) {
    return http.get<PaginatedResponse<Story>>('/stories', { params })
  },

  getRandomStories(limit = 10) {
    return http.get<Story[]>('/stories/random', { params: { limit } })
  },

  getStory(id: string) {
    return http.get<Story>(`/stories/${id}`)
  },

  recordView(id: string) {
    return http.post(`/stories/${id}/view`)
  }
}

// ==================== 语音克隆 API ====================
export const voiceCloneApi = {
  getPresetStories() {
    return http.get<{ stories: PresetStory[] }>('/voice-clone/preset-stories')
  },

  createPreview(audio: File, storyId: string) {
    const formData = new FormData()
    formData.append('audio', audio)
    formData.append('story_id', storyId)
    return http.post<VoiceCloneTask>('/voice-clone/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  getPreviewStatus(taskId: string) {
    return http.get<VoiceCloneTask>(`/voice-clone/preview/${taskId}`)
  },

  getProfiles() {
    return http.get<{ profiles: VoiceProfile[]; total: number }>('/voice-clone/profiles')
  },

  getProfile(id: string) {
    return http.get<VoiceProfile>(`/voice-clone/profiles/${id}`)
  },

  saveProfile(taskId: string, name: string) {
    return http.post<{ profile: VoiceProfile }>('/voice-clone/profiles', {
      task_id: taskId,
      name
    })
  },

  updateProfile(id: string, name: string) {
    return http.put(`/voice-clone/profiles/${id}`, { name })
  },

  deleteProfile(id: string) {
    return http.delete(`/voice-clone/profiles/${id}`)
  }
}

// ==================== 数字人 API ====================
export const digitalHumanApi = {
  createPreview(image: File, options?: {
    audio?: File
    voice_profile_id?: string
    preview_text?: string
  }) {
    const formData = new FormData()
    formData.append('image', image)
    if (options?.audio) {
      formData.append('audio', options.audio)
    }
    if (options?.voice_profile_id) {
      formData.append('voice_profile_id', options.voice_profile_id)
    }
    if (options?.preview_text) {
      formData.append('preview_text', options.preview_text)
    }
    return http.post<DigitalHumanTask>('/digital-human/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  getPreviewStatus(taskId: string) {
    return http.get<DigitalHumanTask>(`/digital-human/preview/${taskId}`)
  },

  getProfiles() {
    return http.get<{ profiles: AvatarProfile[]; total: number }>('/digital-human/profiles')
  },

  getProfile(id: string) {
    return http.get<AvatarProfile>(`/digital-human/profiles/${id}`)
  },

  saveProfile(taskId: string, name: string) {
    return http.post<{ profile: AvatarProfile }>('/digital-human/profiles', {
      task_id: taskId,
      name
    })
  },

  updateProfile(id: string, name: string) {
    return http.put(`/digital-human/profiles/${id}`, { name })
  },

  deleteProfile(id: string) {
    return http.delete(`/digital-human/profiles/${id}`)
  }
}

// ==================== 故事生成 API ====================
export const storyGenerationApi = {
  // 获取故事的说话人信息
  getSpeakers(storyId: string) {
    return http.get<{
      story_id: string
      speaker_count: number
      speakers: Speaker[]
      background_audio_url?: string
      is_analyzed: boolean
      analysis_error?: string
      // 新架构：单人/双人两种分析模式
      single_speaker_analysis?: SingleSpeakerAnalysis
      dual_speaker_analysis?: DualSpeakerAnalysis
    }>(`/story-generation/speakers/${storyId}`)
  },

  // 触发说话人分析
  analyzeStory(storyId: string, numSpeakers?: number) {
    return http.post<{
      story_id: string
      status: string
    }>(`/story-generation/analyze/${storyId}`, null, {
      params: numSpeakers ? { num_speakers: numSpeakers } : undefined
    })
  },

  // 创建任务（支持单说话人和多说话人）
  createJob(data: CreateStoryJobRequest) {
    return http.post<StoryGenerationJob>('/story-generation/jobs', data)
  },

  getJobs(params?: { page?: number; page_size?: number }) {
    return http.get<PaginatedResponse<StoryGenerationJob>>('/story-generation/jobs', { params })
  },

  getJob(id: string) {
    return http.get<StoryGenerationJob>(`/story-generation/jobs/${id}`)
  },

  getSubtitles(jobId: string) {
    return http.get<{ subtitles: any[] }>(`/story-generation/jobs/${jobId}/subtitles`)
  },

  updateSubtitleSelection(jobId: string, selectedIndices: number[]) {
    return http.put(`/story-generation/jobs/${jobId}/subtitles`, {
      selected_indices: selectedIndices
    })
  }
}

// ==================== 有声书 API ====================
export const audiobookApi = {
  getStories(params?: {
    page?: number
    page_size?: number
    language?: string
    category?: string
    age_group?: string
  }) {
    return http.get<PaginatedResponse<AudiobookStory>>('/audiobook/stories', { params })
  },

  getStory(id: string) {
    return http.get<AudiobookStory>(`/audiobook/stories/${id}`)
  },

  createJob(storyId: string, voiceProfileId: string) {
    return http.post<AudiobookJob>('/audiobook/jobs', {
      story_id: storyId,
      voice_profile_id: voiceProfileId
    })
  },

  getJobs(params?: { page?: number; page_size?: number }) {
    return http.get<PaginatedResponse<AudiobookJob>>('/audiobook/jobs', { params })
  },

  getJob(id: string) {
    return http.get<AudiobookJob>(`/audiobook/jobs/${id}`)
  },

  // 用户电子书相关
  getEbooks(params?: { page?: number; page_size?: number }) {
    return http.get<PaginatedResponse<UserEbook>>('/audiobook/ebooks', { params })
  },

  getEbook(id: string) {
    return http.get<UserEbook>(`/audiobook/ebooks/${id}`)
  },

  createEbook(data: { title: string; content: string; language?: string }) {
    return http.post<UserEbook>('/audiobook/ebooks', data)
  },

  updateEbook(id: string, data: { title?: string; content?: string; language?: string }) {
    return http.put(`/audiobook/ebooks/${id}`, data)
  },

  deleteEbook(id: string) {
    return http.delete(`/audiobook/ebooks/${id}`)
  },

  createJobFromEbook(ebookId: string, voiceProfileId: string) {
    return http.post<{ job_id: string; status: string }>(`/audiobook/ebooks/${ebookId}/jobs`, {
      ebook_id: ebookId,
      voice_profile_id: voiceProfileId
    })
  }
}
