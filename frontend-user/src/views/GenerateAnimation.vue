<template>
  <div class="page-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <img src="/logo.png" alt="Echobot" />
        <span>Echobot</span>
      </div>

      <nav class="sidebar-nav">
        <a
          v-for="item in menuItems"
          :key="item.path"
          :class="['nav-item', { active: currentPath === item.path }]"
          @click="navigate(item.path)"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="item.icon"></svg>
          <span class="nav-text">{{ item.name }}</span>
        </a>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">Sign Out</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <header class="topbar">
        <h1 class="page-title">Generate Animation</h1>
        <div class="user-menu" @click="toggleUserMenu">
          <img :src="user?.avatar_url || '/default-avatar.svg'" alt="avatar" class="user-avatar" />
          <span class="user-name">{{ user?.nickname || 'User' }}</span>
          <div v-if="showUserMenu" class="dropdown-menu">
            <a class="dropdown-item" @click="goToProfile">Profile</a>
            <a class="dropdown-item" @click="handleLogout">Sign Out</a>
          </div>
        </div>
      </header>

      <main class="content">
        <!-- 步骤指示器 -->
        <div class="steps-indicator">
          <div :class="['step', { active: step >= 1, completed: step > 1 }]">
            <span class="step-number">1</span>
            <span class="step-label">Select Story</span>
          </div>
          <div class="step-line"></div>
          <div :class="['step', { active: step >= 2, completed: step > 2 }]">
            <span class="step-number">2</span>
            <span class="step-label">Select Voice</span>
          </div>
          <div class="step-line"></div>
          <div :class="['step', { active: step >= 3 }]">
            <span class="step-number">3</span>
            <span class="step-label">Generate</span>
          </div>
        </div>

        <!-- Step 1: 选择故事 -->
        <div v-if="step === 1" class="step-content">
          <h2 class="step-title">Select a Story</h2>
          <p class="step-desc">Choose a story from the library to create your personalized animation</p>

          <div v-if="loadingStories" class="loading-state">Loading stories...</div>
          <div v-else-if="stories.length === 0" class="empty-state">No stories available</div>
          <div v-else class="story-grid">
            <div
              v-for="story in stories"
              :key="story.id"
              :class="['story-card', { selected: selectedStory?.id === story.id }]"
              @click="selectStory(story)"
            >
              <div class="story-thumbnail">
                <img :src="story.thumbnail_url" :alt="story.title" />
                <span class="story-duration">{{ formatDuration(story.duration) }}</span>
                <div class="story-selected-mark" v-if="selectedStory?.id === story.id">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                  </svg>
                </div>
              </div>
              <div class="story-info">
                <h3 class="story-title">{{ story.title }}</h3>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <button
              class="btn btn-primary"
              :disabled="!selectedStory"
              @click="step = 2"
            >
              Next: Select Voice
            </button>
          </div>
        </div>

        <!-- Step 2: 选择声音和头像 -->
        <div v-if="step === 2" class="step-content">
          <h2 class="step-title">Select Voice & Avatar</h2>
          <p class="step-desc">Choose a voice and avatar for your personalized animation</p>

          <!-- 声音选择 -->
          <h3 class="section-title">Voice Profile</h3>
          <div v-if="loadingVoices" class="loading-state">Loading voice profiles...</div>
          <div v-else-if="voiceProfiles.length === 0" class="empty-state">
            <p>No voice profiles found</p>
            <button class="btn btn-outline" @click="navigate('/upload-audio')">
              Create Voice Profile
            </button>
          </div>
          <div v-else class="voice-grid">
            <div
              v-for="voice in voiceProfiles"
              :key="voice.id"
              :class="['voice-card', { selected: selectedVoice?.id === voice.id }]"
              @click="selectVoice(voice)"
            >
              <div class="voice-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
              </div>
              <div class="voice-info">
                <h3 class="voice-name">{{ voice.name || 'Unnamed Voice' }}</h3>
                <div class="voice-preview" v-if="voice.preview_audio_url || voice.reference_audio_url">
                  <audio
                    :src="voice.preview_audio_url || voice.reference_audio_url"
                    controls
                    class="voice-audio"
                    @click.stop
                  ></audio>
                </div>
              </div>
              <div class="voice-selected-mark" v-if="selectedVoice?.id === voice.id">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- 头像选择 -->
          <h3 class="section-title" style="margin-top: 32px;">Avatar Profile (Optional - for Digital Human)</h3>
          <div v-if="loadingAvatars" class="loading-state">Loading avatar profiles...</div>
          <div v-else-if="avatarProfiles.length === 0" class="empty-state">
            <p>No avatar profiles found</p>
            <button class="btn btn-outline" @click="navigate('/upload-photo')">
              Upload Photo
            </button>
          </div>
          <div v-else class="avatar-grid">
            <div
              v-for="avatar in avatarProfiles"
              :key="avatar.id"
              :class="['avatar-card', { selected: selectedAvatar?.id === avatar.id }]"
              @click="selectAvatar(selectedAvatar?.id === avatar.id ? null : avatar)"
            >
              <div class="avatar-thumbnail">
                <img :src="avatar.image_url" :alt="avatar.name" />
                <div class="avatar-selected-mark" v-if="selectedAvatar?.id === avatar.id">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                  </svg>
                </div>
              </div>
              <div class="avatar-info">
                <h3 class="avatar-name">{{ avatar.name || 'Unnamed Avatar' }}</h3>
              </div>
            </div>
          </div>
          <p class="helper-text" v-if="avatarProfiles.length > 0">
            Select an avatar to add a digital human narrator to your video. Skip to generate audio-only.
          </p>

          <div class="step-actions">
            <button class="btn btn-outline" @click="step = 1">Back</button>
            <button
              class="btn btn-primary"
              :disabled="!selectedVoice"
              @click="step = 3"
            >
              Next: Generate
            </button>
          </div>
        </div>

        <!-- Step 3: 生成 -->
        <div v-if="step === 3" class="step-content">
          <h2 class="step-title">Generate Animation</h2>

          <!-- 未开始生成 -->
          <div v-if="!jobId" class="generate-summary">
            <div class="summary-card">
              <h3>Summary</h3>
              <div class="summary-item">
                <span class="summary-label">Story:</span>
                <span class="summary-value">{{ selectedStory?.title }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Voice:</span>
                <span class="summary-value">{{ selectedVoice?.name }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Avatar:</span>
                <span class="summary-value">{{ selectedAvatar?.name || 'None (Audio only)' }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Duration:</span>
                <span class="summary-value">{{ formatDuration(selectedStory?.duration || 0) }}</span>
              </div>
            </div>

            <div class="step-actions">
              <button class="btn btn-outline" @click="step = 2">Back</button>
              <button
                class="btn btn-primary btn-generate"
                :disabled="generating"
                @click="startGeneration"
              >
                {{ generating ? 'Starting...' : 'Start Generation' }}
              </button>
            </div>
          </div>

          <!-- 生成中 -->
          <div v-else class="generation-progress">
            <div class="progress-card">
              <div class="progress-header">
                <span class="progress-status">{{ jobStatus }}</span>
                <span class="progress-percent">{{ jobProgress }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: jobProgress + '%' }"></div>
              </div>
              <div class="progress-step">{{ currentStep }}</div>
            </div>

            <!-- 生成完成 -->
            <div v-if="jobStatus === 'completed'" class="result-container">
              <h3>Generation Complete!</h3>
              <video
                v-if="finalVideoUrl"
                :src="finalVideoUrl"
                controls
                class="result-video"
              ></video>
              <div class="result-actions">
                <a
                  v-if="finalVideoUrl"
                  :href="finalVideoUrl"
                  download
                  class="btn btn-primary"
                >
                  Download Video
                </a>
                <button class="btn btn-outline" @click="resetGeneration">
                  Generate Another
                </button>
              </div>
            </div>

            <!-- 生成失败 -->
            <div v-if="jobStatus === 'failed'" class="error-container">
              <h3>Generation Failed</h3>
              <p class="error-message">{{ jobError }}</p>
              <button class="btn btn-primary" @click="resetGeneration">
                Try Again
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const showUserMenu = ref(false)
const currentPath = ref('/generate')

// 步骤控制
const step = ref(1)

// 数据
const stories = ref<any[]>([])
const voiceProfiles = ref<any[]>([])
const avatarProfiles = ref<any[]>([])
const selectedStory = ref<any>(null)
const selectedVoice = ref<any>(null)
const selectedAvatar = ref<any>(null)

// 加载状态
const loadingStories = ref(false)
const loadingVoices = ref(false)
const loadingAvatars = ref(false)

// 生成状态
const generating = ref(false)
const jobId = ref<string | null>(null)
const jobStatus = ref('')
const jobProgress = ref(0)
const currentStep = ref('')
const jobError = ref('')
const finalVideoUrl = ref('')

let pollInterval: number | null = null

const menuItems = [
  { path: '/dashboard', name: 'Story Library', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { path: '/upload-photo', name: 'Upload Photo', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>' },
  { path: '/upload-audio', name: 'Upload Audio', icon: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>' },
  { path: '/audiobook', name: 'Audiobook', icon: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 7h8"/><path d="M8 11h6"/>' },
  { path: '/generate', name: 'Generate Animation', icon: '<polygon points="5 3 19 12 5 21 5 3"/>' }
]

function navigate(path: string) {
  currentPath.value = path
  router.push(path)
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

function goToProfile() {
  router.push('/profile')
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

async function fetchStories() {
  loadingStories.value = true
  try {
    const response = await api.get('/stories', { params: { page_size: 100 } })
    stories.value = response.data.data.items || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  } finally {
    loadingStories.value = false
  }
}

async function fetchVoiceProfiles() {
  loadingVoices.value = true
  try {
    const response = await api.get('/voice-clone/profiles')
    voiceProfiles.value = response.data.data.profiles || []
  } catch (error) {
    console.error('Failed to fetch voice profiles:', error)
  } finally {
    loadingVoices.value = false
  }
}

async function fetchAvatarProfiles() {
  loadingAvatars.value = true
  try {
    const response = await api.get('/digital-human/profiles')
    avatarProfiles.value = response.data.data.profiles || []
  } catch (error) {
    console.error('Failed to fetch avatar profiles:', error)
  } finally {
    loadingAvatars.value = false
  }
}

function selectStory(story: any) {
  selectedStory.value = story
}

function selectVoice(voice: any) {
  selectedVoice.value = voice
}

function selectAvatar(avatar: any) {
  selectedAvatar.value = avatar
}

async function startGeneration() {
  if (!selectedStory.value || !selectedVoice.value) return

  generating.value = true
  try {
    const response = await api.post('/story-generation/jobs', {
      story_id: selectedStory.value.id,
      voice_profile_id: selectedVoice.value.id,
      avatar_profile_id: selectedAvatar.value?.id || '', // 头像档案（可选）
      replace_all_voice: true
    }, { timeout: 30000 }) // 增加超时时间到30秒

    jobId.value = response.data.data.job_id
    jobStatus.value = 'pending'
    jobProgress.value = 0

    // 开始轮询进度
    startPolling()
  } catch (error: any) {
    console.error('Failed to start generation:', error)
    // 显示更详细的错误信息
    let errorMsg = 'Failed to start generation'
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMsg = error.response.data.message
    } else if (error.message) {
      errorMsg = error.message
    }
    alert(errorMsg)
  } finally {
    generating.value = false
  }
}

function startPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
  }

  pollInterval = window.setInterval(async () => {
    if (!jobId.value) return

    try {
      const response = await api.get(`/story-generation/jobs/${jobId.value}`)
      const job = response.data.data

      jobStatus.value = job.status
      jobProgress.value = job.progress || 0
      currentStep.value = formatStep(job.current_step)
      jobError.value = job.error || ''
      finalVideoUrl.value = job.final_video_url || ''

      // 完成或失败时停止轮询
      if (job.status === 'completed' || job.status === 'failed') {
        stopPolling()
      }
    } catch (error) {
      console.error('Failed to poll job status:', error)
    }
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

function formatStep(step: string): string {
  const stepMap: Record<string, string> = {
    'init': 'Initializing...',
    'extracting_audio': 'Extracting audio from video...',
    'separating_vocals': 'Separating vocals and background music...',
    'transcribing': 'Transcribing speech with word timestamps...',
    'generating_voice': 'Generating cloned voice...',
    'generating_digital_human': 'Generating digital human video...',
    'compositing_video': 'Compositing final video...',
    'completed': 'Completed!'
  }
  return stepMap[step] || step || 'Processing...'
}

function resetGeneration() {
  jobId.value = null
  jobStatus.value = ''
  jobProgress.value = 0
  currentStep.value = ''
  jobError.value = ''
  finalVideoUrl.value = ''
  step.value = 1
}

onMounted(async () => {
  await userStore.fetchProfile()
  await Promise.all([fetchStories(), fetchVoiceProfiles(), fetchAvatarProfiles()])
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-layout {
  display: flex;
  width: 100%;
  height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: #2B5F6C;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 100vh;
  position: sticky;
  top: 0;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.sidebar-logo img {
  width: 28px;
  height: 28px;
  border-radius: 6px;
}

.sidebar-logo span {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: #E8E4D4;
}

.sidebar-nav {
  padding: var(--spacing-sm) 0;
  flex: 1;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  color: rgba(232, 228, 212, 0.85);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin: 2px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border-left-color: #E8E4D4;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
  margin-top: auto;
}

.logout-btn {
  width: 100%;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: var(--font-size-sm);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  position: relative;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name {
  color: var(--color-text-secondary);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--spacing-sm);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  min-width: 120px;
  z-index: 100;
}

.dropdown-item {
  display: block;
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-2xl);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  opacity: 0.5;
}

.step.active {
  opacity: 1;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-dark-tertiary);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.step.active .step-number {
  background: #2B5F6C;
  border-color: #2B5F6C;
  color: #fff;
}

.step.completed .step-number {
  background: var(--color-success);
  border-color: var(--color-success);
  color: #fff;
}

.step-label {
  color: var(--color-text-secondary);
}

.step.active .step-label {
  color: var(--color-text-primary);
}

.step-line {
  width: 60px;
  height: 2px;
  background: var(--color-border);
}

/* 步骤内容 */
.step-content {
  max-width: 900px;
  margin: 0 auto;
}

.step-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  text-align: center;
}

.step-desc {
  color: var(--color-text-secondary);
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

/* 故事网格 */
.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.story-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}

.story-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border);
}

.story-card.selected {
  border-color: #2B5F6C;
}

.story-thumbnail {
  position: relative;
  aspect-ratio: 16/9;
}

.story-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.story-duration {
  position: absolute;
  bottom: var(--spacing-xs);
  right: var(--spacing-xs);
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
}

.story-selected-mark {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);
  width: 24px;
  height: 24px;
  background: #2B5F6C;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.story-selected-mark svg {
  width: 16px;
  height: 16px;
  color: #fff;
}

.story-info {
  padding: var(--spacing-sm);
}

.story-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 声音网格 */
.voice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.voice-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
  text-align: center;
  position: relative;
}

.voice-card:hover {
  border-color: var(--color-border);
  transform: translateY(-2px);
}

.voice-card.selected {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.voice-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto var(--spacing-md);
  background: #2B5F6C;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.voice-name {
  font-size: var(--font-size-base);
  font-weight: 500;
  margin-bottom: var(--spacing-sm);
}

.voice-preview {
  margin-top: var(--spacing-sm);
}

.voice-audio {
  width: 100%;
  height: 32px;
  border-radius: var(--radius-sm);
}

.voice-selected-mark {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  width: 24px;
  height: 24px;
  background: #2B5F6C;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-selected-mark svg {
  width: 16px;
  height: 16px;
  color: #fff;
}

/* 头像网格 */
.avatar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.avatar-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}

.avatar-card:hover {
  border-color: var(--color-border);
  transform: translateY(-2px);
}

.avatar-card.selected {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.avatar-thumbnail {
  position: relative;
  aspect-ratio: 1;
}

.avatar-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-selected-mark {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);
  width: 24px;
  height: 24px;
  background: #2B5F6C;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-selected-mark svg {
  width: 16px;
  height: 16px;
  color: #fff;
}

.avatar-info {
  padding: var(--spacing-sm);
}

.avatar-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-dark-primary);
}

.helper-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-dark-secondary);
  margin-top: var(--spacing-sm);
  text-align: center;
}

/* 操作按钮 */
.step-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.btn {
  padding: var(--spacing-sm) var(--spacing-xl);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: #2B5F6C;
  border: none;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #3D7B7B;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.btn-outline:hover {
  border-color: var(--color-text-secondary);
  color: var(--color-text-primary);
}

.btn-generate {
  padding: var(--spacing-md) var(--spacing-2xl);
  font-size: var(--font-size-lg);
}

/* 摘要卡片 */
.generate-summary {
  max-width: 400px;
  margin: 0 auto;
}

.summary-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.summary-card h3 {
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-lg);
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-label {
  color: var(--color-text-secondary);
}

.summary-value {
  font-weight: 500;
}

/* 进度 */
.generation-progress {
  max-width: 500px;
  margin: 0 auto;
}

.progress-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.progress-status {
  text-transform: capitalize;
  font-weight: 500;
}

.progress-percent {
  color: #2B5F6C;
  font-weight: 600;
}

.progress-bar {
  height: 8px;
  background: var(--color-bg-dark);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-md);
}

.progress-fill {
  height: 100%;
  background: #2B5F6C;
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.progress-step {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  text-align: center;
}

/* 结果 */
.result-container {
  text-align: center;
}

.result-container h3 {
  color: var(--color-success);
  margin-bottom: var(--spacing-lg);
}

.result-video {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
}

/* 错误 */
.error-container {
  text-align: center;
}

.error-container h3 {
  color: var(--color-error);
  margin-bottom: var(--spacing-md);
}

.error-message {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
}

/* 加载/空状态 */
.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.empty-state .btn {
  margin-top: var(--spacing-md);
}
</style>
