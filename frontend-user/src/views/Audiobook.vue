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
        <h1 class="page-title">Audiobook</h1>
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
        <div class="audiobook-container">
          <!-- 标签切换 -->
          <div class="tabs">
            <button
              :class="['tab-btn', { active: activeTab === 'create' }]"
              @click="activeTab = 'create'"
            >
              Create Audiobook
            </button>
            <button
              :class="['tab-btn', { active: activeTab === 'library' }]"
              @click="activeTab = 'library'; fetchMyAudiobooks()"
            >
              My Audiobooks
            </button>
          </div>

          <!-- 创建有声书 -->
          <div v-if="activeTab === 'create'" class="create-section">
            <!-- 步骤指示器 -->
            <div class="steps-indicator">
              <div :class="['step', { active: step >= 1, completed: step > 1 }]">
                <div class="step-number">1</div>
                <span class="step-label">Select Story</span>
              </div>
              <div class="step-line" :class="{ active: step > 1 }"></div>
              <div :class="['step', { active: step >= 2, completed: step > 2 }]">
                <div class="step-number">2</div>
                <span class="step-label">Select Voice</span>
              </div>
              <div class="step-line" :class="{ active: step > 2 }"></div>
              <div :class="['step', { active: step >= 3 }]">
                <div class="step-number">3</div>
                <span class="step-label">Generate</span>
              </div>
            </div>

            <!-- Step 1: 选择故事 -->
            <div v-if="step === 1" class="step-content">
              <h2 class="step-title">Select a Story</h2>
              <p class="step-desc">Choose a story to generate as an audiobook with your cloned voice.</p>

              <div v-if="loadingStories" class="loading-state">
                <div class="spinner"></div>
                <p>Loading stories...</p>
              </div>

              <div v-else-if="stories.length === 0" class="empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                </svg>
                <p>No stories available yet</p>
              </div>

              <div v-else class="stories-grid">
                <div
                  v-for="story in stories"
                  :key="story.id"
                  :class="['story-card', { selected: selectedStory?.id === story.id }]"
                  @click="selectStory(story)"
                >
                  <div class="story-thumbnail" v-if="story.thumbnail_url">
                    <img :src="story.thumbnail_url" :alt="story.title_en" />
                  </div>
                  <div class="story-thumbnail placeholder" v-else>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                    </svg>
                  </div>
                  <div class="story-info">
                    <h3 class="story-title">{{ story.title_en }}</h3>
                    <div class="story-meta">
                      <span class="story-duration">{{ formatDuration(story.estimated_duration) }}</span>
                      <span class="story-category">{{ story.category }}</span>
                    </div>
                  </div>
                  <div v-if="selectedStory?.id === story.id" class="selected-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="step-actions">
                <button
                  class="btn btn-primary"
                  :disabled="!selectedStory"
                  @click="goToStep(2)"
                >
                  Next: Select Voice
                </button>
              </div>
            </div>

            <!-- Step 2: 选择声音档案 -->
            <div v-if="step === 2" class="step-content">
              <h2 class="step-title">Select a Voice Profile</h2>
              <p class="step-desc">Choose the voice you want to use for narrating the story.</p>

              <div v-if="loadingVoices" class="loading-state">
                <div class="spinner"></div>
                <p>Loading voice profiles...</p>
              </div>

              <div v-else-if="voiceProfiles.length === 0" class="empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
                <p>No voice profiles found</p>
                <button class="btn btn-outline" @click="navigate('/upload-audio')">
                  Create Voice Profile
                </button>
              </div>

              <div v-else class="voice-profiles-list">
                <div
                  v-for="voice in voiceProfiles"
                  :key="voice.id"
                  :class="['voice-card', { selected: selectedVoice?.id === voice.id }]"
                  @click="selectVoice(voice)"
                >
                  <div class="voice-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M9 18V5l12-2v13"/>
                      <circle cx="6" cy="18" r="3"/>
                      <circle cx="18" cy="16" r="3"/>
                    </svg>
                  </div>
                  <div class="voice-info">
                    <h3 class="voice-name">{{ voice.name }}</h3>
                    <p class="voice-desc" v-if="voice.description">{{ voice.description }}</p>
                    <span class="voice-date">Created {{ formatDate(voice.created_at) }}</span>
                  </div>
                  <div v-if="selectedVoice?.id === voice.id" class="selected-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="step-actions">
                <button class="btn btn-outline" @click="goToStep(1)">Back</button>
                <button
                  class="btn btn-primary"
                  :disabled="!selectedVoice"
                  @click="goToStep(3)"
                >
                  Next: Generate
                </button>
              </div>
            </div>

            <!-- Step 3: 生成确认 -->
            <div v-if="step === 3" class="step-content">
              <h2 class="step-title">Generate Audiobook</h2>
              <p class="step-desc">Review your selection and generate the audiobook.</p>

              <div class="summary-card">
                <div class="summary-row">
                  <span class="summary-label">Story</span>
                  <span class="summary-value">{{ selectedStory?.title_en }}</span>
                </div>
                <div class="summary-row">
                  <span class="summary-label">Estimated Duration</span>
                  <span class="summary-value">{{ formatDuration(selectedStory?.estimated_duration) }}</span>
                </div>
                <div class="summary-row">
                  <span class="summary-label">Voice Profile</span>
                  <span class="summary-value">{{ selectedVoice?.name }}</span>
                </div>
              </div>

              <!-- 生成中状态 -->
              <div v-if="generating" class="generating-state">
                <div class="progress-container">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ progress }}%</span>
                </div>
                <p class="generating-hint">{{ currentStepText }}</p>
              </div>

              <!-- 错误提示 -->
              <div v-if="generateError" class="error-message">
                <p>{{ generateError }}</p>
                <button class="btn btn-outline" @click="generateError = ''">Try Again</button>
              </div>

              <!-- 生成完成 -->
              <div v-if="generatedJob" class="success-section">
                <div class="success-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                </div>
                <h3>Audiobook Generated!</h3>
                <p>Your audiobook is ready to listen.</p>
                <audio :src="generatedJob.audio_url" controls class="audio-player"></audio>
              </div>

              <div class="step-actions">
                <button class="btn btn-outline" @click="goToStep(2)" :disabled="generating">Back</button>
                <button
                  v-if="!generatedJob && !generating"
                  class="btn btn-primary"
                  @click="generateAudiobook"
                >
                  Generate Audiobook
                </button>
                <button
                  v-if="generatedJob"
                  class="btn btn-primary"
                  @click="resetAndCreate"
                >
                  Create Another
                </button>
              </div>
            </div>
          </div>

          <!-- 我的有声书 -->
          <div v-if="activeTab === 'library'" class="library-section">
            <div v-if="loadingAudiobooks" class="loading-state">
              <div class="spinner"></div>
              <p>Loading your audiobooks...</p>
            </div>

            <div v-else-if="myAudiobooks.length === 0" class="empty-state">
              <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                <path d="M8 7h8"/>
                <path d="M8 11h6"/>
              </svg>
              <p>No audiobooks yet</p>
              <button class="btn btn-primary" @click="activeTab = 'create'">
                Create Your First Audiobook
              </button>
            </div>

            <div v-else class="audiobooks-list">
              <div
                v-for="job in myAudiobooks"
                :key="job.id"
                class="audiobook-card"
              >
                <div class="audiobook-header">
                  <h3 class="audiobook-title">{{ job.story_title }}</h3>
                  <span :class="['status-badge', job.status]">{{ job.status }}</span>
                </div>
                <div class="audiobook-meta">
                  <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M9 18V5l12-2v13"/>
                      <circle cx="6" cy="18" r="3"/>
                      <circle cx="18" cy="16" r="3"/>
                    </svg>
                    {{ job.voice_name }}
                  </span>
                  <span class="meta-item" v-if="job.duration">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    {{ formatDuration(job.duration) }}
                  </span>
                  <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="4" width="18" height="18" rx="2"/>
                      <line x1="16" y1="2" x2="16" y2="6"/>
                      <line x1="8" y1="2" x2="8" y2="6"/>
                      <line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    {{ formatDate(job.created_at) }}
                  </span>
                </div>

                <!-- 进度条 (处理中) -->
                <div v-if="job.status === 'processing'" class="job-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: job.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ job.progress }}% - {{ job.current_step }}</span>
                </div>

                <!-- 播放器 (完成) -->
                <div v-if="job.status === 'completed' && job.audio_url" class="audiobook-player">
                  <audio :src="job.audio_url" controls class="audio-player"></audio>
                </div>

                <!-- 错误信息 (失败) -->
                <div v-if="job.status === 'failed'" class="job-error">
                  <p>{{ job.error || 'Generation failed' }}</p>
                </div>
              </div>
            </div>

            <!-- 分页 -->
            <div v-if="totalAudiobooks > pageSize" class="pagination">
              <button
                class="page-btn"
                :disabled="currentPage <= 1"
                @click="goToPage(currentPage - 1)"
              >
                Previous
              </button>
              <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
              <button
                class="page-btn"
                :disabled="currentPage >= totalPages"
                @click="goToPage(currentPage + 1)"
              >
                Next
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
const currentPath = ref('/audiobook')

// 标签页
const activeTab = ref<'create' | 'library'>('create')

// 步骤控制
const step = ref(1)

// 故事数据
const stories = ref<any[]>([])
const loadingStories = ref(false)
const selectedStory = ref<any | null>(null)

// 声音档案
const voiceProfiles = ref<any[]>([])
const loadingVoices = ref(false)
const selectedVoice = ref<any | null>(null)

// 生成状态
const generating = ref(false)
const progress = ref(0)
const currentStepText = ref('Initializing...')
const jobId = ref<string | null>(null)
const generatedJob = ref<any | null>(null)
const generateError = ref('')

// 我的有声书
const myAudiobooks = ref<any[]>([])
const loadingAudiobooks = ref(false)
const currentPage = ref(1)
const pageSize = 10
const totalAudiobooks = ref(0)

let pollInterval: number | null = null

const totalPages = computed(() => Math.ceil(totalAudiobooks.value / pageSize))

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

function formatDuration(seconds: number | undefined): string {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// 获取故事列表
async function fetchStories() {
  loadingStories.value = true
  try {
    const response = await api.get('/audiobook/stories', {
      params: { page: 1, page_size: 50 }
    })
    stories.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  } finally {
    loadingStories.value = false
  }
}

// 获取声音档案
async function fetchVoiceProfiles() {
  loadingVoices.value = true
  try {
    const response = await api.get('/voice-clone/profiles')
    voiceProfiles.value = response.data.data?.profiles || []
  } catch (error) {
    console.error('Failed to fetch voice profiles:', error)
  } finally {
    loadingVoices.value = false
  }
}

// 获取我的有声书
async function fetchMyAudiobooks() {
  loadingAudiobooks.value = true
  try {
    const response = await api.get('/audiobook/jobs', {
      params: { page: currentPage.value, page_size: pageSize }
    })
    myAudiobooks.value = response.data.data?.items || []
    totalAudiobooks.value = response.data.data?.total || 0
  } catch (error) {
    console.error('Failed to fetch audiobooks:', error)
  } finally {
    loadingAudiobooks.value = false
  }
}

function selectStory(story: any) {
  selectedStory.value = story
}

function selectVoice(voice: any) {
  selectedVoice.value = voice
}

function goToStep(newStep: number) {
  if (newStep === 2 && voiceProfiles.value.length === 0) {
    fetchVoiceProfiles()
  }
  step.value = newStep
}

function goToPage(page: number) {
  currentPage.value = page
  fetchMyAudiobooks()
}

// 生成有声书
async function generateAudiobook() {
  if (!selectedStory.value || !selectedVoice.value) return

  generating.value = true
  progress.value = 0
  currentStepText.value = 'Starting generation...'
  generateError.value = ''
  generatedJob.value = null

  try {
    const response = await api.post('/audiobook/jobs', {
      story_id: selectedStory.value.id,
      voice_profile_id: selectedVoice.value.id
    })

    jobId.value = response.data.data?.job_id
    if (jobId.value) {
      startPolling()
    }
  } catch (error: any) {
    generating.value = false
    generateError.value = error.response?.data?.detail || error.response?.data?.message || 'Failed to start generation'
  }
}

function startPolling() {
  pollInterval = window.setInterval(async () => {
    if (!jobId.value) return

    try {
      const response = await api.get(`/audiobook/jobs/${jobId.value}`)
      const data = response.data.data

      progress.value = data.progress || 0
      currentStepText.value = getStepText(data.current_step, data.progress)

      if (data.status === 'completed') {
        stopPolling()
        generating.value = false
        generatedJob.value = data
      } else if (data.status === 'failed') {
        stopPolling()
        generating.value = false
        generateError.value = data.error || 'Generation failed'
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 3000) // 每 3 秒轮询
}

function getStepText(step: string | undefined, progress: number): string {
  const steps: Record<string, string> = {
    'init': 'Initializing...',
    'tts': 'Generating voice narration...',
    'mixing': 'Mixing audio...',
    'completed': 'Completed!'
  }
  return steps[step || 'init'] || `Processing... ${progress}%`
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

function resetAndCreate() {
  step.value = 1
  selectedStory.value = null
  selectedVoice.value = null
  generatedJob.value = null
  generateError.value = ''
  progress.value = 0
  jobId.value = null
}

onMounted(async () => {
  await userStore.fetchProfile()
  fetchStories()
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

/* Audiobook Container */
.audiobook-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* Tabs */
.tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
}

.tab-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  border-bottom: 2px solid transparent;
  margin-bottom: -9px;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  color: #2B5F6C;
  border-bottom-color: #2B5F6C;
}

/* Steps Indicator */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-2xl);
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-bg-dark-tertiary);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.step.active .step-number {
  background: #2B5F6C;
  border-color: #2B5F6C;
  color: #fff;
}

.step.completed .step-number {
  background: var(--color-success);
  border-color: var(--color-success);
}

.step-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.step.active .step-label {
  color: var(--color-text-primary);
}

.step-line {
  width: 80px;
  height: 2px;
  background: var(--color-border);
  margin: 0 var(--spacing-md);
  margin-bottom: 20px;
}

.step-line.active {
  background: #2B5F6C;
}

/* Step Content */
.step-content {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
}

.step-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.step-desc {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

/* Stories Grid */
.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.story-card {
  background: var(--color-bg-dark-tertiary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.story-card:hover {
  border-color: var(--color-border-light);
  transform: translateY(-2px);
}

.story-card.selected {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.story-thumbnail {
  width: 100%;
  height: 120px;
  overflow: hidden;
  background: var(--color-bg-dark);
  display: flex;
  align-items: center;
  justify-content: center;
}

.story-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.story-thumbnail.placeholder svg {
  width: 40px;
  height: 40px;
  color: var(--color-text-muted);
}

.story-info {
  padding: var(--spacing-md);
}

.story-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.story-meta {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.selected-badge {
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

.selected-badge svg {
  width: 14px;
  height: 14px;
  color: #fff;
}

/* Voice Profiles List */
.voice-profiles-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.voice-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.voice-card:hover {
  border-color: var(--color-border-light);
}

.voice-card.selected {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.voice-icon {
  width: 48px;
  height: 48px;
  background: rgba(43, 95, 108, 0.2);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.voice-icon svg {
  width: 24px;
  height: 24px;
  color: #2B5F6C;
}

.voice-info {
  flex: 1;
}

.voice-name {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.voice-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.voice-date {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Summary Card */
.summary-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  color: var(--color-text-secondary);
}

.summary-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

/* Generating State */
.generating-state {
  text-align: center;
  padding: var(--spacing-xl);
}

.progress-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #2B5F6C;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  min-width: 40px;
}

.generating-hint {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* Success Section */
.success-section {
  text-align: center;
  padding: var(--spacing-xl);
  background: rgba(52, 199, 89, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xl);
}

.success-icon {
  width: 64px;
  height: 64px;
  background: var(--color-success);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-md);
}

.success-icon svg {
  width: 32px;
  height: 32px;
  color: #fff;
}

.success-section h3 {
  font-size: var(--font-size-lg);
  color: var(--color-success);
  margin-bottom: var(--spacing-sm);
}

.success-section p {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
}

/* Error Message */
.error-message {
  text-align: center;
  padding: var(--spacing-lg);
  background: rgba(255, 59, 48, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xl);
}

.error-message p {
  color: var(--color-error);
  margin-bottom: var(--spacing-md);
}

/* Audio Player */
.audio-player {
  width: 100%;
  height: 40px;
}

/* Step Actions */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

/* Buttons */
.btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: #2B5F6C;
  border: none;
  color: #fff;
}

.btn-primary:hover {
  background: #3d7a8a;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.btn-outline:hover {
  background: var(--color-bg-dark-hover);
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: #2B5F6C;
  border-radius: 50%;
  margin: 0 auto var(--spacing-md);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--spacing-md);
  color: var(--color-text-muted);
}

.empty-state p {
  margin-bottom: var(--spacing-lg);
}

/* Audiobooks List */
.audiobooks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.audiobook-card {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.audiobook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.audiobook-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.pending {
  background: rgba(255, 149, 0, 0.2);
  color: var(--color-warning);
}

.status-badge.processing {
  background: rgba(0, 122, 255, 0.2);
  color: var(--color-info);
}

.status-badge.completed {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.status-badge.failed {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.audiobook-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.meta-item svg {
  width: 16px;
  height: 16px;
}

.job-progress {
  margin-bottom: var(--spacing-md);
}

.audiobook-player {
  margin-top: var(--spacing-md);
}

.job-error {
  padding: var(--spacing-md);
  background: rgba(255, 59, 48, 0.1);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-md);
}

.job-error p {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  margin: 0;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  background: var(--color-bg-dark-hover);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
