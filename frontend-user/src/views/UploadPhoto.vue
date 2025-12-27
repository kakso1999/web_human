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
        <h1 class="page-title">Digital Avatar</h1>
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
        <div class="avatar-container">
          <!-- 步骤指示器 -->
          <div class="steps-indicator">
            <div :class="['step', { active: step >= 1, completed: step > 1 }]">
              <div class="step-number">1</div>
              <span class="step-label">Upload Photo</span>
            </div>
            <div class="step-line" :class="{ active: step > 1 }"></div>
            <div :class="['step', { active: step >= 2 }]">
              <div class="step-number">2</div>
              <span class="step-label">Preview</span>
            </div>
          </div>

          <!-- Step 1: 上传照片 -->
          <div v-if="step === 1" class="step-content">
            <h2 class="step-title">Upload Your Photo</h2>
            <p class="step-desc">Upload a clear portrait photo to create your digital avatar. The photo should show your face clearly with good lighting.</p>

            <div
              class="upload-area"
              :class="{ 'has-file': imageFile, 'dragging': isDragging }"
              @click="triggerFileInput"
              @drop.prevent="handleDrop"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
            >
              <input
                type="file"
                ref="fileInput"
                accept="image/*"
                @change="handleFileSelect"
                hidden
              />
              <div v-if="!imageFile" class="upload-placeholder">
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span class="upload-text">Click or drag photo here</span>
                <span class="upload-hint">Support JPG, PNG (Clear portrait photo)</span>
              </div>
              <div v-else class="file-info">
                <img :src="imagePreviewUrl" alt="preview" class="image-preview" />
                <div class="file-details">
                  <span class="file-name">{{ imageFile.name }}</span>
                  <span class="file-size">{{ formatFileSize(imageFile.size) }}</span>
                </div>
                <button class="remove-btn" @click.stop="removeFile">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="photo-requirements">
              <h4>Photo Requirements:</h4>
              <ul>
                <li>Clear front-facing portrait</li>
                <li>Good lighting, no shadows on face</li>
                <li>Neutral expression or slight smile</li>
                <li>Plain background preferred</li>
              </ul>
            </div>

            <div class="step-actions">
              <button
                class="btn btn-primary"
                :disabled="!imageFile"
                @click="goToStep(2)"
              >
                Next: Generate Avatar
              </button>
            </div>
          </div>

          <!-- Step 2: 生成预览 -->
          <div v-if="step === 2" class="step-content">
            <h2 class="step-title">Generate Digital Avatar</h2>
            <p class="step-desc">We'll create an animated digital avatar from your photo.</p>

            <div class="preview-summary">
              <div class="summary-item">
                <span class="summary-label">Your Photo:</span>
                <div class="summary-image">
                  <img :src="imagePreviewUrl" alt="preview" />
                  <span>{{ imageFile?.name }}</span>
                </div>
              </div>
            </div>

            <!-- 音频来源选择 -->
            <div v-if="!generating && !generatedVideoUrl" class="audio-source-section">
              <h4 class="section-title">Voice for Avatar</h4>
              <p class="section-desc">Choose how your avatar will speak:</p>

              <div class="audio-options">
                <label class="audio-option" :class="{ active: audioSource === 'default' }">
                  <input type="radio" v-model="audioSource" value="default" />
                  <span class="option-content">
                    <span class="option-title">Default Voice</span>
                    <span class="option-desc">Use system default voice</span>
                  </span>
                </label>

                <label class="audio-option" :class="{ active: audioSource === 'upload' }">
                  <input type="radio" v-model="audioSource" value="upload" />
                  <span class="option-content">
                    <span class="option-title">Upload Audio</span>
                    <span class="option-desc">Upload your own audio file</span>
                  </span>
                </label>

                <label class="audio-option" :class="{ active: audioSource === 'voice_profile' }">
                  <input type="radio" v-model="audioSource" value="voice_profile" />
                  <span class="option-content">
                    <span class="option-title">My Saved Voice</span>
                    <span class="option-desc">Use a cloned voice profile</span>
                  </span>
                </label>
              </div>

              <!-- 上传音频 -->
              <div v-if="audioSource === 'upload'" class="audio-upload-area">
                <input
                  type="file"
                  ref="audioInput"
                  accept="audio/*"
                  @change="handleAudioSelect"
                  hidden
                />
                <div
                  class="upload-box"
                  :class="{ 'has-file': audioFile }"
                  @click="$refs.audioInput?.click()"
                >
                  <div v-if="!audioFile" class="upload-placeholder">
                    <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M9 18V5l12-2v13"/>
                      <circle cx="6" cy="18" r="3"/>
                      <circle cx="18" cy="16" r="3"/>
                    </svg>
                    <span>Click to upload audio file</span>
                  </div>
                  <div v-else class="file-selected">
                    <span class="file-name">{{ audioFile.name }}</span>
                    <span class="file-size">{{ formatFileSize(audioFile.size) }}</span>
                  </div>
                </div>
              </div>

              <!-- 选择已保存的声音 -->
              <div v-if="audioSource === 'voice_profile'" class="voice-profile-section">
                <div v-if="loadingProfiles" class="loading-profiles">
                  Loading voice profiles...
                </div>
                <div v-else-if="voiceProfiles.length === 0" class="no-profiles">
                  <p>No saved voice profiles. Please create one in "Upload Audio" first.</p>
                  <button class="btn btn-outline btn-sm" @click="$router.push('/upload-audio')">
                    Go to Upload Audio
                  </button>
                </div>
                <div v-else class="profile-selector">
                  <select v-model="selectedVoiceProfileId" class="voice-select">
                    <option value="">Select a voice profile...</option>
                    <option v-for="profile in voiceProfiles" :key="profile.id" :value="profile.id">
                      {{ profile.name }}
                    </option>
                  </select>
                  <textarea
                    v-model="previewText"
                    placeholder="Enter text for avatar to speak..."
                    class="preview-text-input"
                    rows="2"
                  ></textarea>
                </div>
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
              <p class="generating-hint">
                <span v-if="progress < 30">Uploading and detecting face...</span>
                <span v-else-if="progress < 60">Creating digital avatar...</span>
                <span v-else>Generating preview video... This may take 1-2 minutes.</span>
              </p>
            </div>

            <!-- 生成结果 -->
            <div v-if="generatedVideoUrl" class="result-section">
              <h3 class="result-title">Your Digital Avatar Preview</h3>
              <video :src="generatedVideoUrl" controls class="video-player"></video>
              <p class="result-hint">This is how your digital avatar will look in story animations!</p>

              <!-- 保存按钮 -->
              <div class="save-section" v-if="!saved">
                <input
                  v-model="avatarName"
                  type="text"
                  placeholder="Enter a name (e.g., Dad's Avatar)"
                  class="name-input"
                />
                <button class="btn btn-success" @click="saveAvatar" :disabled="!avatarName || saving">
                  {{ saving ? 'Saving...' : 'Save to My Avatars' }}
                </button>
              </div>
              <div v-else class="saved-message">
                Avatar saved successfully!
              </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="generateError" class="error-message">
              <p>{{ generateError }}</p>
              <button class="btn btn-outline" @click="generateError = ''">Try Again</button>
            </div>

            <div class="step-actions">
              <button class="btn btn-outline" @click="goToStep(1)">Back</button>
              <button
                v-if="!generatedVideoUrl && !generating"
                class="btn btn-primary"
                @click="generatePreview"
              >
                Generate Avatar
              </button>
              <button
                v-if="generatedVideoUrl"
                class="btn btn-primary"
                @click="resetAll"
              >
                Create Another Avatar
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const showUserMenu = ref(false)
const currentPath = ref('/upload-photo')

// 步骤控制
const step = ref(1)

// Step 1: 照片上传
const imageFile = ref<File | null>(null)
const imagePreviewUrl = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

// Step 2: 生成预览
const generating = ref(false)
const progress = ref(0)
const taskId = ref<string | null>(null)
const generatedVideoUrl = ref<string | null>(null)
const generateError = ref('')

// 保存相关
const avatarName = ref('')
const saving = ref(false)
const saved = ref(false)

// 音频来源相关
const audioSource = ref<'default' | 'upload' | 'voice_profile'>('default')
const audioFile = ref<File | null>(null)
const audioInput = ref<HTMLInputElement | null>(null)
const voiceProfiles = ref<Array<{ id: string; name: string }>>([])
const selectedVoiceProfileId = ref('')
const previewText = ref('Hello, I am your digital avatar. Nice to meet you!')
const loadingProfiles = ref(false)

let pollInterval: number | null = null

// 监听音频来源变化
watch(audioSource, (newVal) => {
  if (newVal === 'voice_profile') {
    loadVoiceProfiles()
  }
})

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
    setImageFile(input.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files?.[0] && files[0].type.startsWith('image/')) {
    setImageFile(files[0])
  }
}

function setImageFile(file: File) {
  imageFile.value = file
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
  imagePreviewUrl.value = URL.createObjectURL(file)
}

function removeFile() {
  imageFile.value = null
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = null
  }
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 音频文件处理
function handleAudioSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    audioFile.value = input.files[0]
  }
}

async function loadVoiceProfiles() {
  if (voiceProfiles.value.length > 0) return // 已加载

  loadingProfiles.value = true
  try {
    const response = await api.get('/voice-clone/profiles')
    voiceProfiles.value = response.data.data?.profiles || []
  } catch (error) {
    console.error('Failed to load voice profiles:', error)
    voiceProfiles.value = []
  } finally {
    loadingProfiles.value = false
  }
}

// 步骤切换
function goToStep(newStep: number) {
  step.value = newStep
  // 进入 step 2 时，如果选择了 voice_profile，加载声音档案
  if (newStep === 2 && audioSource.value === 'voice_profile') {
    loadVoiceProfiles()
  }
}

// Step 2: 生成预览
async function generatePreview() {
  if (!imageFile.value) return

  // 验证音频选项
  if (audioSource.value === 'upload' && !audioFile.value) {
    generateError.value = 'Please upload an audio file'
    return
  }
  if (audioSource.value === 'voice_profile') {
    if (!selectedVoiceProfileId.value) {
      generateError.value = 'Please select a voice profile'
      return
    }
    if (!previewText.value.trim()) {
      generateError.value = 'Please enter text for the avatar to speak'
      return
    }
  }

  generating.value = true
  progress.value = 0
  generateError.value = ''
  generatedVideoUrl.value = null
  saved.value = false
  avatarName.value = ''

  try {
    const formData = new FormData()
    formData.append('image', imageFile.value)

    // 添加音频相关参数
    if (audioSource.value === 'upload' && audioFile.value) {
      formData.append('audio', audioFile.value)
    } else if (audioSource.value === 'voice_profile') {
      formData.append('voice_profile_id', selectedVoiceProfileId.value)
      formData.append('preview_text', previewText.value)
    }

    const response = await api.post('/digital-human/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    taskId.value = response.data.data?.task_id
    if (taskId.value) {
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
      const response = await api.get(`/digital-human/preview/${taskId.value}`)
      const data = response.data.data

      progress.value = data.progress || 0

      if (data.status === 'completed') {
        stopPolling()
        generating.value = false
        generatedVideoUrl.value = data.video_url
      } else if (data.status === 'failed') {
        stopPolling()
        generating.value = false
        generateError.value = data.error || 'Generation failed. Please use a clear portrait photo.'
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function saveAvatar() {
  if (!taskId.value || !avatarName.value) return

  saving.value = true
  try {
    await api.post('/digital-human/profiles', {
      task_id: taskId.value,
      name: avatarName.value
    })
    saved.value = true
  } catch (error: any) {
    generateError.value = error.response?.data?.message || 'Failed to save avatar'
  } finally {
    saving.value = false
  }
}

function resetAll() {
  step.value = 1
  imageFile.value = null
  imagePreviewUrl.value = null
  generatedVideoUrl.value = null
  generateError.value = ''
  taskId.value = null
  progress.value = 0
  avatarName.value = ''
  saved.value = false
}

onMounted(async () => {
  await userStore.fetchProfile()
})

onUnmounted(() => {
  stopPolling()
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
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

.avatar-container {
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
  width: 100px;
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

.image-preview {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-md);
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

/* Photo Requirements */
.photo-requirements {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
}

.photo-requirements h4 {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.photo-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.photo-requirements li {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  padding: var(--spacing-xs) 0;
  padding-left: var(--spacing-md);
  position: relative;
}

.photo-requirements li::before {
  content: "*";
  position: absolute;
  left: 0;
  color: #2B5F6C;
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
  align-items: center;
  gap: var(--spacing-md);
}

.summary-label {
  color: var(--color-text-secondary);
}

.summary-image {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.summary-image img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.summary-image span {
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

.video-player {
  width: 100%;
  max-width: 400px;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
}

.result-hint {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-lg);
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

.saved-message {
  color: var(--color-success);
  font-weight: 500;
  margin-top: var(--spacing-lg);
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

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.btn-outline:hover {
  background: var(--color-bg-dark-hover);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
}

/* Audio Source Section */
.audio-source-section {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
}

.section-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.section-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.audio-options {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.audio-option {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex: 1;
  min-width: 150px;
}

.audio-option:hover {
  border-color: #2B5F6C;
}

.audio-option.active {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.1);
}

.audio-option input[type="radio"] {
  margin-top: 2px;
  accent-color: #2B5F6C;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.option-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Audio Upload Area */
.audio-upload-area {
  margin-top: var(--spacing-md);
}

.upload-box {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-box:hover {
  border-color: #2B5F6C;
  background: rgba(43, 95, 108, 0.05);
}

.upload-box.has-file {
  border-style: solid;
  border-color: #2B5F6C;
}

.file-selected {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.file-selected .file-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.file-selected .file-size {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Voice Profile Section */
.voice-profile-section {
  margin-top: var(--spacing-md);
}

.loading-profiles,
.no-profiles {
  text-align: center;
  padding: var(--spacing-md);
  color: var(--color-text-secondary);
}

.no-profiles p {
  margin-bottom: var(--spacing-md);
}

.profile-selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.voice-select {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.voice-select:focus {
  outline: none;
  border-color: #2B5F6C;
}

.preview-text-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  resize: vertical;
  min-height: 60px;
}

.preview-text-input:focus {
  outline: none;
  border-color: #2B5F6C;
}
</style>
