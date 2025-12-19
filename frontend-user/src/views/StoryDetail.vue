<template>
  <div class="story-detail-page">
    <div class="story-container" v-if="story">
      <!-- 顶部导航 -->
      <div class="story-header">
        <button class="back-btn" @click="goBack">Back</button>
        <h1 class="story-title">{{ story.title }}</h1>
      </div>

      <!-- 视频播放器 -->
      <div class="video-section">
        <video
          ref="videoPlayer"
          class="video-player"
          :src="story.video_url"
          :poster="story.thumbnail_url || '/placeholder.svg'"
          controls
          @timeupdate="handleTimeUpdate"
          @loadedmetadata="handleMetadataLoaded"
        ></video>
      </div>

      <!-- 视频信息 -->
      <div class="story-info">
        <div class="info-row">
          <span class="info-label">Duration</span>
          <span class="info-value">{{ formatDuration(story.duration) }}</span>
        </div>
        <div class="info-row" v-if="story.category">
          <span class="info-label">Category</span>
          <span class="info-value">{{ story.category.name }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Created</span>
          <span class="info-value">{{ formatDate(story.created_at) }}</span>
        </div>
      </div>

      <!-- 描述 -->
      <div class="story-description" v-if="story.description">
        <h3>Description</h3>
        <p>{{ story.description }}</p>
      </div>

      <!-- 操作按钮 -->
      <div class="story-actions">
        <button class="btn btn-primary" @click="downloadVideo" :disabled="downloading">
          {{ downloading ? 'Downloading...' : 'Download Video' }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-state" v-else-if="loading">
      <p>Loading...</p>
    </div>

    <!-- 错误状态 -->
    <div class="error-state" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="fetchStory">Retry</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()

interface Category {
  id: string
  name: string
}

interface Story {
  id: string
  title: string
  description: string | null
  video_url: string
  thumbnail_url: string | null
  duration: number
  category: Category | null
  created_at: string
}

const story = ref<Story | null>(null)
const loading = ref(true)
const error = ref('')
const downloading = ref(false)
const videoPlayer = ref<HTMLVideoElement>()

function goBack() {
  router.push('/dashboard')
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function handleTimeUpdate() {
  // 可以用于保存播放进度
}

function handleMetadataLoaded() {
  // 视频元数据加载完成
}

async function downloadVideo() {
  if (!story.value?.video_url) return

  downloading.value = true
  try {
    const response = await fetch(story.value.video_url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${story.value.title}.mp4`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Download failed:', err)
  } finally {
    downloading.value = false
  }
}

async function fetchStory() {
  const storyId = route.params.id as string
  if (!storyId) {
    error.value = 'Invalid story ID'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await api.get(`/stories/${storyId}`)
    story.value = response.data.data
  } catch (err: any) {
    error.value = err.response?.data?.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStory()
})
</script>

<style scoped>
.story-detail-page {
  min-height: 100vh;
  padding: var(--spacing-xl);
}

.story-container {
  max-width: 900px;
  margin: 0 auto;
}

.story-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.back-btn {
  color: var(--color-text-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
}

.story-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  flex: 1;
}

.video-section {
  margin-bottom: var(--spacing-xl);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-bg-dark-tertiary);
}

.video-player {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.story-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}

.info-row {
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

.story-description {
  padding: var(--spacing-lg);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}

.story-description h3 {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.story-description p {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.story-actions {
  display: flex;
  gap: var(--spacing-md);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: var(--spacing-lg);
}

.loading-state p,
.error-state p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
}
</style>
