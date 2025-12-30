<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <img src="/logo.png" alt="Echobot" />
        <span>管理后台</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: item.path === '/stories' }]"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">退出</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="back-btn" @click="goBack">返回</button>
          <h1 class="page-title">编辑故事</h1>
        </div>
      </header>

      <main class="content" v-if="story">
        <div class="edit-grid">
          <!-- 左侧：视频预览 -->
          <div class="preview-section">
            <div class="video-container">
              <video
                v-if="story.video_url"
                :src="story.video_url"
                :poster="story.thumbnail_url || '/placeholder.svg'"
                controls
                class="video-player"
              ></video>
              <div v-else class="no-video">
                <p>暂无视频</p>
              </div>
            </div>

            <div class="video-info">
              <div class="info-item">
                <span class="info-label">时长</span>
                <span class="info-value">{{ formatDuration(story.duration) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间</span>
                <span class="info-value">{{ formatDate(story.created_at) }}</span>
              </div>
            </div>

            <!-- 英文标题 -->
            <div class="title-en-section" v-if="story.title_en">
              <div class="section-header">
                <span class="section-title">英文标题 (AI生成)</span>
              </div>
              <p class="title-en-text">{{ story.title_en }}</p>
            </div>

            <!-- 字幕显示 -->
            <div class="subtitle-section" v-if="story.subtitles && story.subtitles.length > 0">
              <div class="section-header">
                <span class="section-title">字幕内容</span>
                <span class="subtitle-count">{{ story.subtitles.length }} 条</span>
              </div>
              <div class="subtitle-list">
                <div
                  v-for="(segment, index) in story.subtitles"
                  :key="index"
                  class="subtitle-item"
                >
                  <span class="subtitle-time">
                    {{ formatSubtitleTime(segment.start) }} - {{ formatSubtitleTime(segment.end) }}
                  </span>
                  <span class="subtitle-text">{{ segment.text }}</span>
                </div>
              </div>
            </div>

            <!-- 无字幕提示 -->
            <div class="subtitle-section empty" v-else-if="!story.subtitles">
              <div class="section-header">
                <span class="section-title">字幕内容</span>
              </div>
              <p class="no-subtitle">字幕正在生成中，请稍后刷新查看...</p>
            </div>
          </div>

          <!-- 右侧：编辑表单 -->
          <div class="edit-section">
            <form @submit.prevent="handleSave">
              <div class="form-group">
                <label>标题</label>
                <input v-model="form.title" type="text" class="input" required />
              </div>

              <div class="form-group">
                <label>描述</label>
                <textarea v-model="form.description" class="input textarea"></textarea>
              </div>

              <div class="form-group">
                <label>分类</label>
                <select v-model="form.category_id" class="input">
                  <option value="">选择分类</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label>状态</label>
                <select v-model="form.status" class="input">
                  <option value="active">正常</option>
                  <option value="inactive">已下架</option>
                </select>
              </div>

              <div class="form-group">
                <label>更换缩略图</label>
                <div class="file-upload">
                  <input
                    type="file"
                    ref="thumbnailInput"
                    accept="image/*"
                    @change="handleThumbnailSelect"
                    hidden
                  />
                  <button type="button" class="btn btn-outline" @click="($refs.thumbnailInput as HTMLInputElement)?.click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="upload-icon">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    选择图片
                  </button>
                  <span class="file-name" v-if="form.thumbnail">{{ form.thumbnail.name }}</span>
                </div>
              </div>

              <div class="form-group">
                <label>更换视频</label>
                <div class="file-upload">
                  <input
                    type="file"
                    ref="videoInput"
                    accept="video/*"
                    @change="handleVideoSelect"
                    hidden
                  />
                  <button type="button" class="btn btn-outline" @click="($refs.videoInput as HTMLInputElement)?.click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="upload-icon">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    选择视频
                  </button>
                  <span class="file-name" v-if="form.video">{{ form.video.name }}</span>
                </div>
              </div>

              <p v-if="message" :class="['message', messageType]">{{ message }}</p>

              <div class="form-actions">
                <button type="submit" class="btn btn-accent" :disabled="saving">
                  {{ saving ? '保存中...' : '保存修改' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>

      <!-- 加载状态 -->
      <div class="loading-state" v-else-if="loading">
        <p>加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div class="error-state" v-else-if="error">
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="fetchStory">重试</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin'
import api from '../api'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()

interface Category {
  id: string
  name: string
}

interface SubtitleSegment {
  start: number
  end: number
  text: string
}

interface Story {
  id: string
  title: string
  title_en: string | null
  description: string | null
  video_url: string
  audio_url: string | null
  thumbnail_url: string | null
  duration: number
  status: string
  category: Category | null
  subtitles: SubtitleSegment[] | null
  subtitle_text: string | null
  created_at: string
}

const story = ref<Story | null>(null)
const categories = ref<Category[]>([])
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const form = ref({
  title: '',
  description: '',
  category_id: '',
  status: 'active',
  thumbnail: null as File | null,
  video: null as File | null
})

const menuItems = [
  {
    path: '/dashboard',
    name: '仪表盘',
    icon: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
  },
  {
    path: '/users',
    name: '用户管理',
    icon: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
  },
  {
    path: '/stories',
    name: '故事管理',
    icon: '<svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>'
  },
  {
    path: '/audiobooks',
    name: '有声书管理',
    icon: '<svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>'
  }
]

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatSubtitleTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function goBack() {
  router.push('/stories')
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

function handleThumbnailSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    form.value.thumbnail = input.files[0]
  }
}

function handleVideoSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    form.value.video = input.files[0]
  }
}

function showMessage(msg: string, type: 'success' | 'error') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

async function fetchStory() {
  const storyId = route.params.id as string
  if (!storyId) {
    error.value = '无效的故事ID'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await api.get(`/admin/stories/${storyId}`)
    story.value = response.data.data

    // Populate form
    form.value.title = story.value!.title
    form.value.description = story.value!.description || ''
    form.value.category_id = story.value!.category?.id || ''
    form.value.status = story.value!.status
  } catch (err: any) {
    error.value = err.response?.data?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const response = await api.get('/stories/categories')
    categories.value = response.data.data || []
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

async function handleSave() {
  if (!story.value) return

  saving.value = true

  try {
    const formData = new FormData()
    formData.append('title', form.value.title)
    formData.append('status', form.value.status)

    if (form.value.description) {
      formData.append('description', form.value.description)
    }

    if (form.value.category_id) {
      formData.append('category_id', form.value.category_id)
    }

    if (form.value.thumbnail) {
      formData.append('thumbnail', form.value.thumbnail)
    }

    if (form.value.video) {
      formData.append('video', form.value.video)
    }

    await api.put(`/admin/stories/${story.value.id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    showMessage('保存成功', 'success')
    await fetchStory()
  } catch (err: any) {
    showMessage(err.response?.data?.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchStory()
  fetchCategories()
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
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
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.back-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

.edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
}

.preview-section {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.video-container {
  margin-bottom: var(--spacing-lg);
}

.video-player {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-md);
  background: #000;
}

.no-video {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
}

.video-info {
  display: flex;
  gap: var(--spacing-xl);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

/* 英文标题部分 */
.title-en-section {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.section-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.title-en-text {
  font-size: var(--font-size-lg);
  color: var(--color-accent);
  font-weight: 500;
  margin: 0;
}

/* 字幕部分 */
.subtitle-section {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.subtitle-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  background: var(--color-bg-dark-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.subtitle-list {
  max-height: 300px;
  overflow-y: auto;
  padding-right: var(--spacing-sm);
}

.subtitle-list::-webkit-scrollbar {
  width: 6px;
}

.subtitle-list::-webkit-scrollbar-track {
  background: var(--color-bg-dark-tertiary);
  border-radius: 3px;
}

.subtitle-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.subtitle-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}

.subtitle-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-dark);
}

.subtitle-item:last-child {
  border-bottom: none;
}

.subtitle-time {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
  font-family: monospace;
  color: var(--color-accent);
  background: var(--color-bg-dark-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  height: fit-content;
}

.subtitle-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.5;
}

.no-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-style: italic;
  margin: 0;
}

.edit-section {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-xs);
}

.textarea {
  min-height: 120px;
  resize: vertical;
}

.message {
  font-size: var(--font-size-sm);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-md);
}

.message.success {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.message.error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.file-upload {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-outline:hover {
  background: var(--color-bg-dark-hover);
  border-color: var(--color-accent);
  color: var(--color-text-primary);
}

.upload-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.file-name {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-actions {
  margin-top: var(--spacing-lg);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: var(--spacing-lg);
}

.loading-state p,
.error-state p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
}

@media (max-width: 1024px) {
  .edit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
