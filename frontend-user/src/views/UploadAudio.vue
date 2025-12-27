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
        <h1 class="page-title">Voice Clone</h1>
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
        <div class="voice-clone-container">
          <!-- 步骤指示器 -->
          <div class="steps-indicator">
            <div :class="['step', { active: step >= 1, completed: step > 1 }]">
              <div class="step-number">1</div>
              <span class="step-label">Upload Voice</span>
            </div>
            <div class="step-line" :class="{ active: step > 1 }"></div>
            <div :class="['step', { active: step >= 2, completed: step > 2 }]">
              <div class="step-number">2</div>
              <span class="step-label">Select Story</span>
            </div>
            <div class="step-line" :class="{ active: step > 2 }"></div>
            <div :class="['step', { active: step >= 3 }]">
              <div class="step-number">3</div>
              <span class="step-label">Preview</span>
            </div>
          </div>

          <!-- Step 1: 上传音频 -->
          <div v-if="step === 1" class="step-content">
            <h2 class="step-title">Upload Your Voice Sample</h2>
            <p class="step-desc">Upload a 10-15 second audio clip of your voice. Speak clearly without background noise.</p>

            <div
              class="upload-area"
              :class="{ 'has-file': audioFile, 'dragging': isDragging }"
              @click="triggerFileInput"
              @drop.prevent="handleDrop"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
            >
              <input
                type="file"
                ref="fileInput"
                accept="audio/*"
                @change="handleFileSelect"
                hidden
              />
              <div v-if="!audioFile" class="upload-placeholder">
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span class="upload-text">Click or drag audio file here</span>
                <span class="upload-hint">Support MP3, WAV (10-15 seconds)</span>
              </div>
              <div v-else class="file-info">
                <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
                <div class="file-details">
                  <span class="file-name">{{ audioFile.name }}</span>
                  <span class="file-size">{{ formatFileSize(audioFile.size) }}</span>
                </div>
                <button class="remove-btn" @click.stop="removeFile">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- 音频预览播放器 -->
            <div v-if="audioFile && audioPreviewUrl" class="audio-preview">
              <span class="preview-label">Preview your audio:</span>
              <audio :src="audioPreviewUrl" controls class="audio-player"></audio>
            </div>

            <div class="step-actions">
              <button
                class="btn btn-primary"
                :disabled="!audioFile"
                @click="goToStep(2)"
              >
                Next: Select Story
              </button>
            </div>
          </div>

          <!-- Step 2: 选择故事 -->
          <div v-if="step === 2" class="step-content">
            <h2 class="step-title">Select a Story</h2>
            <p class="step-desc">Choose a story to narrate with your cloned voice.</p>

            <div v-if="loadingStories" class="loading-state">
              <p>Loading stories...</p>
            </div>

            <div v-else class="stories-grid">
              <div
                v-for="story in presetStories"
                :key="story.id"
                :class="['story-card', { selected: selectedStory?.id === story.id }]"
                @click="selectStory(story)"
              >
                <div class="story-header">
                  <h3 class="story-title">{{ story.title }}</h3>
                  <span class="story-duration">~{{ story.estimated_duration }}s</span>
                </div>
                <p class="story-preview">{{ story.preview_text }}</p>
              </div>
            </div>

            <div class="step-actions">
              <button class="btn btn-outline" @click="goToStep(1)">Back</button>
              <button
                class="btn btn-primary"
                :disabled="!selectedStory"
                @click="goToStep(3)"
              >
                Next: Generate Preview
              </button>
            </div>
          </div>

          <!-- Step 3: 生成预览 -->
          <div v-if="step === 3" class="step-content">
            <h2 class="step-title">Generate Voice Preview</h2>
            <p class="step-desc">Generate a preview of your cloned voice narrating the selected story.</p>

            <div class="preview-summary">
              <div class="summary-item">
                <span class="summary-label">Your Voice:</span>
                <span class="summary-value">{{ audioFile?.name }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Story:</span>
                <span class="summary-value">{{ selectedStory?.title }}</span>
              </div>
            </div>

            <!-- 生成状态 -->
            <div v-if="generating" class="generating-state">
              <div class="progress-container">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ progress }}%</span>
              </div>
              <p class="generating-hint">Generating voice clone... This may take 30-60 seconds.</p>
            </div>

            <!-- 生成结果 -->
            <div v-if="generatedAudioUrl" class="result-section">
              <h3 class="result-title">Your Cloned Voice Preview</h3>
              <audio :src="generatedAudioUrl" controls class="audio-player result-player"></audio>
              <p class="result-hint">Listen to how your voice sounds narrating the story!</p>

              <!-- 保存按钮 -->
              <div class="save-section" v-if="!saved">
                <input
                  v-model="voiceProfileName"
                  type="text"
                  placeholder="Enter a name (e.g., Dad's Voice)"
                  class="name-input"
                />
                <button class="btn btn-success" @click="saveVoiceProfile" :disabled="!voiceProfileName || saving">
                  {{ saving ? 'Saving...' : 'Save to My Voices' }}
                </button>
              </div>
              <div v-else class="saved-message">
                Voice profile saved successfully!
              </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="generateError" class="error-message">
              <p>{{ generateError }}</p>
              <button class="btn btn-outline" @click="generateError = ''">Try Again</button>
            </div>

            <div class="step-actions">
              <button class="btn btn-outline" @click="goToStep(2)">Back</button>
              <button
                v-if="!generatedAudioUrl && !generating"
                class="btn btn-primary"
                @click="generatePreview"
              >
                Generate Preview
              </button>
              <button
                v-if="generatedAudioUrl"
                class="btn btn-primary"
                @click="resetAll"
              >
                Try Another Voice
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
const currentPath = ref('/upload-audio')

// 步骤控制
const step = ref(1)

// Step 1: 音频上传
const audioFile = ref<File | null>(null)
const audioPreviewUrl = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

// Step 2: 故事选择
const presetStories = ref<any[]>([])
const selectedStory = ref<any | null>(null)
const loadingStories = ref(false)

// Step 3: 生成预览
const generating = ref(false)
const progress = ref(0)
const taskId = ref<string | null>(null)
const generatedAudioUrl = ref<string | null>(null)
const generateError = ref('')

// 保存相关
const voiceProfileName = ref('')
const saving = ref(false)
const saved = ref(false)

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

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Step 1: 文件处理
function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    setAudioFile(input.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files?.[0] && files[0].type.startsWith('audio/')) {
    setAudioFile(files[0])
  }
}

function setAudioFile(file: File) {
  audioFile.value = file
  // 创建预览 URL
  if (audioPreviewUrl.value) {
    URL.revokeObjectURL(audioPreviewUrl.value)
  }
  audioPreviewUrl.value = URL.createObjectURL(file)
}

function removeFile() {
  audioFile.value = null
  if (audioPreviewUrl.value) {
    URL.revokeObjectURL(audioPreviewUrl.value)
    audioPreviewUrl.value = null
  }
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Step 2: 获取预设故事
async function fetchPresetStories() {
  loadingStories.value = true
  try {
    const response = await api.get('/voice-clone/preset-stories')
    presetStories.value = response.data.data?.stories || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  } finally {
    loadingStories.value = false
  }
}

function selectStory(story: any) {
  selectedStory.value = story
}

// 步骤切换
function goToStep(newStep: number) {
  if (newStep === 2 && presetStories.value.length === 0) {
    fetchPresetStories()
  }
  step.value = newStep
}

// Step 3: 生成预览
async function generatePreview() {
  if (!audioFile.value || !selectedStory.value) return

  generating.value = true
  progress.value = 0
  generateError.value = ''
  generatedAudioUrl.value = null

  try {
    // 上传音频并创建任务
    const formData = new FormData()
    formData.append('audio', audioFile.value)
    formData.append('story_id', selectedStory.value.id)

    const response = await api.post('/voice-clone/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    taskId.value = response.data.data?.task_id
    if (taskId.value) {
      // 开始轮询状态
      startPolling()
    }
  } catch (error: any) {
    generating.value = false
    generateError.value = error.response?.data?.message || 'Failed to start generation'
  }
}

function startPolling() {
  pollInterval = window.setInterval(async () => {
    if (!taskId.value) return

    try {
      const response = await api.get(`/voice-clone/preview/${taskId.value}`)
      const data = response.data.data

      progress.value = data.progress || 0

      if (data.status === 'completed') {
        stopPolling()
        generating.value = false
        generatedAudioUrl.value = data.audio_url
      } else if (data.status === 'failed') {
        stopPolling()
        generating.value = false
        generateError.value = data.error || 'Generation failed'
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 2000) // 每 2 秒轮询一次
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

function resetAll() {
  step.value = 1
  audioFile.value = null
  audioPreviewUrl.value = null
  selectedStory.value = null
  generatedAudioUrl.value = null
  generateError.value = ''
  taskId.value = null
  progress.value = 0
  voiceProfileName.value = ''
  saving.value = false
  saved.value = false
}

async function saveVoiceProfile() {
  if (!taskId.value || !voiceProfileName.value) return

  saving.value = true
  try {
    await api.post('/voice-clone/profiles', {
      task_id: taskId.value,
      name: voiceProfileName.value
    })
    saved.value = true
  } catch (error: any) {
    generateError.value = error.response?.data?.message || 'Failed to save voice profile'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await userStore.fetchProfile()
})

onUnmounted(() => {
  stopPolling()
  if (audioPreviewUrl.value) {
    URL.revokeObjectURL(audioPreviewUrl.value)
  }
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

/* Voice Clone Container */
.voice-clone-container {
  max-width: 800px;
  margin: 0 auto;
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

/* Upload Area */
.upload-area {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: center;
}

.upload-area:hover,
.upload-area.dragging {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.upload-area.has-file {
  border-style: solid;
  border-color: #2B5F6C;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-muted);
}

.upload-text {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.upload-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.file-icon {
  width: 40px;
  height: 40px;
  color: #2B5F6C;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-name {
  display: block;
  font-weight: 500;
  color: var(--color-text-primary);
}

.file-size {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.remove-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 59, 48, 0.2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: rgba(255, 59, 48, 0.4);
}

.remove-btn svg {
  width: 16px;
  height: 16px;
  color: var(--color-error);
}

/* Audio Preview */
.audio-preview {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
}

.preview-label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.audio-player {
  width: 100%;
  height: 40px;
}

/* Stories Grid */
.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.story-card {
  background: var(--color-bg-dark-tertiary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.story-card:hover {
  border-color: var(--color-border-light);
}

.story-card.selected {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.story-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
}

.story-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
}

.story-duration {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  background: var(--color-bg-dark);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.story-preview {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Preview Summary */
.preview-summary {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
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

/* Result Section */
.result-section {
  text-align: center;
  padding: var(--spacing-xl);
  background: rgba(43, 95, 108, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xl);
}

.result-title {
  font-size: var(--font-size-lg);
  color: #2B5F6C;
  margin-bottom: var(--spacing-md);
}

.result-player {
  margin-bottom: var(--spacing-md);
}

.result-hint {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
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

.loading-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

/* Save Section */
.save-section {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
  align-items: center;
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.name-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  width: 200px;
}

.name-input:focus {
  outline: none;
  border-color: #2B5F6C;
}

.btn-success {
  background: var(--color-success);
  border: none;
  color: #fff;
}

.btn-success:hover {
  opacity: 0.9;
}

.btn-success:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.saved-message {
  color: var(--color-success);
  font-weight: 500;
  margin-top: var(--spacing-lg);
}
</style>
