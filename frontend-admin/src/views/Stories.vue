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
          :class="['nav-item', { active: currentPath === item.path }]"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <header class="topbar">
        <h1 class="page-title">故事管理</h1>
        <div class="topbar-actions">
          <input
            v-model="searchQuery"
            type="text"
            class="input search-input"
            placeholder="搜索故事标题"
            @input="handleSearch"
          />
          <button class="btn btn-outline" @click="showBatchUploadModal = true">
            批量上传
          </button>
          <button class="btn btn-accent" @click="showCreateModal = true">
            新建故事
          </button>
        </div>
      </header>

      <!-- 批量操作栏 -->
      <div class="batch-actions-bar" v-if="selectedStories.length > 0">
        <span class="selected-count">已选择 {{ selectedStories.length }} 项</span>
        <div class="batch-buttons">
          <button class="btn btn-outline btn-sm" @click="handleBatchPublish">
            批量上架
          </button>
          <button class="btn btn-outline btn-sm" @click="handleBatchUnpublish">
            批量下架
          </button>
          <button class="btn btn-danger btn-sm" @click="handleBatchDelete">
            批量删除
          </button>
          <button class="btn btn-outline btn-sm" @click="clearSelection">
            取消选择
          </button>
        </div>
      </div>

      <main class="content">
        <div class="card">
          <table class="table">
            <thead>
              <tr>
                <th class="checkbox-col">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                </th>
                <th>缩略图</th>
                <th>标题</th>
                <th>时长</th>
                <th>分类</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="story in stories" :key="story.id">
                <td class="checkbox-col">
                  <input
                    type="checkbox"
                    :checked="selectedStories.includes(story.id)"
                    @change="toggleStorySelection(story.id)"
                  />
                </td>
                <td>
                  <div class="thumb-container">
                    <img
                      :src="story.thumbnail_url || '/placeholder.svg'"
                      class="story-thumb"
                      :alt="story.title"
                    />
                    <div v-if="story.status === 'processing'" class="processing-overlay">
                      <div class="spinner"></div>
                    </div>
                  </div>
                </td>
                <td>{{ story.title || '处理中...' }}</td>
                <td>{{ formatDuration(story.duration) }}</td>
                <td>{{ story.category?.name || '-' }}</td>
                <td>
                  <span :class="['status-badge', story.status]">
                    {{ getStatusLabel(story.status) }}
                  </span>
                </td>
                <td>{{ formatDate(story.created_at) }}</td>
                <td>
                  <div class="actions">
                    <button class="btn btn-outline btn-sm" @click="editStory(story.id)">
                      编辑
                    </button>
                    <button
                      class="btn btn-danger btn-sm"
                      @click="handleDeleteStory(story.id)"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 分页 -->
          <div class="pagination" v-if="totalPages > 1">
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              @click="changePage(currentPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="changePage(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </main>
    </div>

    <!-- 创建故事弹窗（单个上传） -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal">
        <h2 class="modal-title">新建故事</h2>

        <form @submit.prevent="handleCreateStory">
          <div class="form-group">
            <label>视频文件</label>
            <div class="video-upload-area" @click="triggerVideoInput" :class="{ 'has-file': newStory.video }">
              <input
                type="file"
                ref="videoInput"
                accept="video/*"
                @change="handleVideoSelect"
                hidden
              />
              <div v-if="!newStory.video" class="upload-placeholder">
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span>点击选择视频文件</span>
                <span class="upload-hint">支持 MP4、WebM 格式</span>
              </div>
              <div v-else class="file-selected">
                <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="23 7 16 12 23 17 23 7"/>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
                <div class="file-details">
                  <span class="file-name">{{ newStory.video.name }}</span>
                  <span class="file-size">{{ formatFileSize(newStory.video.size) }}</span>
                </div>
                <button type="button" class="remove-file" @click.stop="removeVideo">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>分类</label>
            <div class="category-select">
              <select v-model="newStory.category_id" class="input" v-if="!showNewCategory">
                <option value="">选择分类</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
              <input
                v-else
                v-model="newCategoryName"
                type="text"
                class="input"
                placeholder="输入新分类名称"
              />
              <button
                type="button"
                class="btn btn-outline btn-sm"
                @click="toggleNewCategory"
              >
                {{ showNewCategory ? '选择已有' : '+ 新建分类' }}
              </button>
            </div>
          </div>

          <p class="upload-tips">上传后将自动提取缩略图、生成字幕和标题</p>

          <p v-if="createError" class="error-msg">{{ createError }}</p>

          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="closeCreateModal">
              取消
            </button>
            <button type="submit" class="btn btn-accent" :disabled="creating || !newStory.video">
              {{ creating ? '上传中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 批量上传弹窗 -->
    <div v-if="showBatchUploadModal" class="modal-overlay" @click.self="closeBatchUploadModal">
      <div class="modal modal-lg">
        <h2 class="modal-title">批量上传视频</h2>

        <div class="form-group">
          <label>选择分类</label>
          <div class="category-select">
            <select v-model="batchUpload.category_id" class="input" v-if="!showBatchNewCategory">
              <option value="">选择分类</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
            <input
              v-else
              v-model="batchNewCategoryName"
              type="text"
              class="input"
              placeholder="输入新分类名称"
            />
            <button
              type="button"
              class="btn btn-outline btn-sm"
              @click="toggleBatchNewCategory"
            >
              {{ showBatchNewCategory ? '选择已有' : '+ 新建分类' }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>选择视频文件（可多选）</label>
          <div
            class="batch-upload-area"
            @click="triggerBatchVideoInput"
            @drop.prevent="handleBatchDrop"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            :class="{ 'dragging': isDragging, 'has-files': batchUpload.videos.length > 0 }"
          >
            <input
              type="file"
              ref="batchVideoInput"
              accept="video/*"
              multiple
              @change="handleBatchVideoSelect"
              hidden
            />
            <div v-if="batchUpload.videos.length === 0" class="upload-placeholder">
              <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>点击或拖拽选择多个视频文件</span>
              <span class="upload-hint">支持 MP4、WebM 格式，可同时选择多个文件</span>
            </div>
          </div>
        </div>

        <!-- 已选择的文件列表 -->
        <div v-if="batchUpload.videos.length > 0" class="batch-file-list">
          <div class="batch-file-header">
            <span>已选择 {{ batchUpload.videos.length }} 个文件</span>
            <button type="button" class="btn btn-outline btn-sm" @click="clearBatchVideos">
              清空
            </button>
          </div>
          <div class="batch-files">
            <div
              v-for="(file, index) in batchUpload.videos"
              :key="index"
              class="batch-file-item"
            >
              <svg class="file-icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="23 7 16 12 23 17 23 7"/>
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
              </svg>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <button type="button" class="remove-file-sm" @click="removeBatchVideo(index)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="batchUpload.uploading" class="batch-progress">
          <div class="progress-header">
            <span>上传进度</span>
            <span>{{ batchUpload.completed }} / {{ batchUpload.total }}</span>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: `${(batchUpload.completed / batchUpload.total) * 100}%` }"
            ></div>
          </div>
          <div class="progress-items">
            <div
              v-for="(item, index) in batchUpload.items"
              :key="index"
              :class="['progress-item', item.status]"
            >
              <span class="item-name">{{ item.filename }}</span>
              <span class="item-status">{{ getUploadStatusLabel(item.status) }}</span>
            </div>
          </div>
        </div>

        <p v-if="batchUpload.error" class="error-msg">{{ batchUpload.error }}</p>

        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline"
            @click="closeBatchUploadModal"
            :disabled="batchUpload.uploading"
          >
            {{ batchUpload.uploading ? '上传中...' : '取消' }}
          </button>
          <button
            type="button"
            class="btn btn-accent"
            @click="handleBatchUpload"
            :disabled="batchUpload.uploading || batchUpload.videos.length === 0"
          >
            {{ batchUpload.uploading ? '上传中...' : `开始上传 (${batchUpload.videos.length} 个)` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin'
import api from '../api'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()

const currentPath = computed(() => route.path)

interface Category {
  id: string
  name: string
}

interface Story {
  id: string
  title: string
  thumbnail_url: string | null
  duration: number
  status: string
  category: Category | null
  created_at: string
}

interface BatchUploadItem {
  filename: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  story_id: string | null
  error: string | null
}

const stories = ref<Story[]>([])
const categories = ref<Category[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20
const searchQuery = ref('')
let searchTimeout: number | null = null

// 选择的故事
const selectedStories = ref<string[]>([])

// 单个上传
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const showNewCategory = ref(false)
const newCategoryName = ref('')
const videoInput = ref<HTMLInputElement | null>(null)
const newStory = ref({
  category_id: '',
  video: null as File | null
})

// 批量上传
const showBatchUploadModal = ref(false)
const showBatchNewCategory = ref(false)
const batchNewCategoryName = ref('')
const batchVideoInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const batchUpload = ref({
  category_id: '',
  videos: [] as File[],
  uploading: false,
  batch_id: '',
  total: 0,
  completed: 0,
  failed: 0,
  items: [] as BatchUploadItem[],
  error: ''
})

// 自动刷新定时器（处理中的视频）
let refreshTimer: number | null = null
let batchStatusTimer: number | null = null

const menuItems = [
  { path: '/dashboard', name: '仪表盘', icon: '仪' },
  { path: '/users', name: '用户管理', icon: '用' },
  { path: '/stories', name: '故事管理', icon: '事' }
]

// 计算是否全选
const isAllSelected = computed(() => {
  if (stories.value.length === 0) return false
  return stories.value.every(s => selectedStories.value.includes(s.id))
})

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: '正常',
    inactive: '已下架',
    processing: '处理中'
  }
  return labels[status] || status
}

function getUploadStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    uploading: '上传中',
    processing: '处理中',
    completed: '完成',
    failed: '失败'
  }
  return labels[status] || status
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

function handleSearch() {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = window.setTimeout(() => {
    currentPage.value = 1
    fetchStories()
  }, 300)
}

// 选择相关
function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedStories.value = []
  } else {
    selectedStories.value = stories.value.map(s => s.id)
  }
}

function toggleStorySelection(id: string) {
  const index = selectedStories.value.indexOf(id)
  if (index > -1) {
    selectedStories.value.splice(index, 1)
  } else {
    selectedStories.value.push(id)
  }
}

function clearSelection() {
  selectedStories.value = []
}

// 批量操作
async function handleBatchPublish() {
  if (selectedStories.value.length === 0) return
  if (!confirm(`确定要上架选中的 ${selectedStories.value.length} 个故事吗？`)) return

  try {
    await api.post('/admin/stories/batch-publish', selectedStories.value)
    await fetchStories()
    clearSelection()
  } catch (error) {
    console.error('Batch publish failed:', error)
  }
}

async function handleBatchUnpublish() {
  if (selectedStories.value.length === 0) return
  if (!confirm(`确定要下架选中的 ${selectedStories.value.length} 个故事吗？`)) return

  try {
    await api.post('/admin/stories/batch-unpublish', selectedStories.value)
    await fetchStories()
    clearSelection()
  } catch (error) {
    console.error('Batch unpublish failed:', error)
  }
}

async function handleBatchDelete() {
  if (selectedStories.value.length === 0) return
  if (!confirm(`确定要删除选中的 ${selectedStories.value.length} 个故事吗？此操作不可恢复！`)) return

  try {
    await api.delete('/admin/stories/batch', { data: selectedStories.value })
    await fetchStories()
    clearSelection()
  } catch (error) {
    console.error('Batch delete failed:', error)
  }
}

async function fetchStories() {
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await api.get('/admin/stories', { params })
    const data = response.data.data

    stories.value = data.items
    totalPages.value = Math.ceil(data.total / pageSize)
  } catch (error) {
    console.error('Failed to fetch stories:', error)
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

function changePage(page: number) {
  currentPage.value = page
  fetchStories()
}

function editStory(id: string) {
  router.push(`/stories/${id}`)
}

// 单个上传相关
function handleVideoSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    newStory.value.video = input.files[0]
  }
}

function triggerVideoInput() {
  videoInput.value?.click()
}

function removeVideo() {
  newStory.value.video = null
  if (videoInput.value) {
    videoInput.value.value = ''
  }
}

function toggleNewCategory() {
  showNewCategory.value = !showNewCategory.value
  if (!showNewCategory.value) {
    newCategoryName.value = ''
  }
}

function closeCreateModal() {
  showCreateModal.value = false
  showNewCategory.value = false
  newCategoryName.value = ''
  createError.value = ''
  newStory.value = { category_id: '', video: null }
  if (videoInput.value) {
    videoInput.value.value = ''
  }
}

async function handleCreateStory() {
  if (!newStory.value.video) return

  creating.value = true
  createError.value = ''

  try {
    let categoryId = newStory.value.category_id

    // If creating a new category
    if (showNewCategory.value && newCategoryName.value.trim()) {
      const categoryResponse = await api.post('/admin/categories', {
        name: newCategoryName.value.trim(),
        name_en: newCategoryName.value.trim()
      })
      categoryId = categoryResponse.data.data.id
    }

    const formData = new FormData()
    formData.append('video', newStory.value.video)

    if (categoryId) {
      formData.append('category_id', categoryId)
    }

    await api.post('/admin/stories', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    closeCreateModal()
    await fetchStories()
    await fetchCategories()
  } catch (error: any) {
    console.error('Failed to create story:', error)
    createError.value = error.response?.data?.message || '创建失败，请重试'
  } finally {
    creating.value = false
  }
}

// 批量上传相关
function triggerBatchVideoInput() {
  batchVideoInput.value?.click()
}

function handleBatchVideoSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    addBatchVideos(Array.from(input.files))
  }
}

function handleBatchDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    const videoFiles = Array.from(event.dataTransfer.files).filter(
      f => f.type.startsWith('video/')
    )
    addBatchVideos(videoFiles)
  }
}

function addBatchVideos(files: File[]) {
  batchUpload.value.videos.push(...files)
}

function removeBatchVideo(index: number) {
  batchUpload.value.videos.splice(index, 1)
}

function clearBatchVideos() {
  batchUpload.value.videos = []
  if (batchVideoInput.value) {
    batchVideoInput.value.value = ''
  }
}

function toggleBatchNewCategory() {
  showBatchNewCategory.value = !showBatchNewCategory.value
  if (!showBatchNewCategory.value) {
    batchNewCategoryName.value = ''
  }
}

function closeBatchUploadModal() {
  if (batchUpload.value.uploading) return

  showBatchUploadModal.value = false
  showBatchNewCategory.value = false
  batchNewCategoryName.value = ''
  batchUpload.value = {
    category_id: '',
    videos: [],
    uploading: false,
    batch_id: '',
    total: 0,
    completed: 0,
    failed: 0,
    items: [],
    error: ''
  }
  if (batchVideoInput.value) {
    batchVideoInput.value.value = ''
  }
  if (batchStatusTimer) {
    clearInterval(batchStatusTimer)
    batchStatusTimer = null
  }
}

async function handleBatchUpload() {
  if (batchUpload.value.videos.length === 0) return

  batchUpload.value.uploading = true
  batchUpload.value.error = ''

  try {
    let categoryId = batchUpload.value.category_id

    // If creating a new category
    if (showBatchNewCategory.value && batchNewCategoryName.value.trim()) {
      const categoryResponse = await api.post('/admin/categories', {
        name: batchNewCategoryName.value.trim(),
        name_en: batchNewCategoryName.value.trim()
      })
      categoryId = categoryResponse.data.data.id
      await fetchCategories()
    }

    const formData = new FormData()
    for (const video of batchUpload.value.videos) {
      formData.append('videos', video)
    }
    if (categoryId) {
      formData.append('category_id', categoryId)
    }

    const response = await api.post('/admin/stories/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    const { batch_id, total } = response.data.data
    batchUpload.value.batch_id = batch_id
    batchUpload.value.total = total
    batchUpload.value.items = batchUpload.value.videos.map(v => ({
      filename: v.name,
      status: 'pending' as const,
      story_id: null,
      error: null
    }))

    // 开始轮询状态
    startBatchStatusPolling()

  } catch (error: any) {
    console.error('Failed to start batch upload:', error)
    batchUpload.value.error = error.response?.data?.message || '批量上传失败，请重试'
    batchUpload.value.uploading = false
  }
}

function startBatchStatusPolling() {
  batchStatusTimer = window.setInterval(async () => {
    try {
      const response = await api.get(`/admin/stories/batch/${batchUpload.value.batch_id}`)
      const data = response.data.data

      batchUpload.value.completed = data.completed
      batchUpload.value.failed = data.failed
      batchUpload.value.items = data.items

      // 如果全部完成，停止轮询
      if (data.status === 'completed') {
        if (batchStatusTimer) {
          clearInterval(batchStatusTimer)
          batchStatusTimer = null
        }
        batchUpload.value.uploading = false
        await fetchStories()
      }
    } catch (error) {
      console.error('Failed to get batch status:', error)
    }
  }, 2000)
}

async function handleDeleteStory(id: string) {
  if (!confirm('确定要删除此故事吗？此操作不可恢复。')) return

  try {
    await api.delete(`/admin/stories/${id}`)
    await fetchStories()
  } catch (error) {
    console.error('Failed to delete story:', error)
  }
}

onMounted(() => {
  fetchStories()
  fetchCategories()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  if (batchStatusTimer) {
    clearInterval(batchStatusTimer)
  }
})

// 检查是否有处理中的视频
function hasProcessingStories(): boolean {
  return stories.value.some(s => s.status === 'processing')
}

// 启动自动刷新
function startAutoRefresh() {
  if (refreshTimer) return
  refreshTimer = window.setInterval(() => {
    if (hasProcessingStories()) {
      fetchStories()
    }
  }, 5000) // 每5秒检查一次
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-bg-dark-secondary);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-logo img {
  width: 32px;
  height: 32px;
}

.sidebar-logo span {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-md) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.nav-item:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-bg-dark-tertiary);
  color: var(--color-text-primary);
  border-left: 3px solid var(--color-accent);
}

.nav-icon {
  font-size: var(--font-size-lg);
}

.sidebar-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.logout-btn {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.logout-btn:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
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

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.search-input {
  width: 250px;
  padding: var(--spacing-sm) var(--spacing-md);
}

/* 批量操作栏 */
.batch-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--color-bg-dark-tertiary);
  border-bottom: 1px solid var(--color-border);
}

.selected-count {
  color: var(--color-accent);
  font-weight: 500;
}

.batch-buttons {
  display: flex;
  gap: var(--spacing-sm);
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

/* 表格复选框列 */
.checkbox-col {
  width: 40px;
  text-align: center;
}

.checkbox-col input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.story-thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.thumb-container {
  position: relative;
  width: 80px;
  height: 45px;
}

.processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

.status-badge.active {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.status-badge.inactive {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.status-badge.processing {
  background: rgba(255, 159, 10, 0.2);
  color: var(--color-warning);
}

.actions {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-sm {
  padding: 4px 8px;
  font-size: var(--font-size-sm);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  cursor: pointer;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-secondary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-lg {
  max-width: 700px;
}

.modal-title {
  font-size: var(--font-size-xl);
  margin-bottom: var(--spacing-lg);
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
  min-height: 100px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.category-select {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.category-select select,
.category-select input {
  flex: 1;
}

.file-info {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.error-msg {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-sm);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Video Upload Area */
.video-upload-area {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.video-upload-area:hover {
  border-color: var(--color-accent);
  background: rgba(45, 107, 107, 0.05);
}

.video-upload-area.has-file {
  border-style: solid;
  border-color: var(--color-accent);
  background: rgba(45, 107, 107, 0.1);
}

/* Batch Upload Area */
.batch-upload-area {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.batch-upload-area:hover,
.batch-upload-area.dragging {
  border-color: var(--color-accent);
  background: rgba(45, 107, 107, 0.1);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-secondary);
}

.upload-placeholder .upload-icon {
  width: 48px;
  height: 48px;
  stroke: var(--color-text-muted);
}

.upload-placeholder span {
  font-size: var(--font-size-base);
}

.upload-hint {
  font-size: var(--font-size-sm) !important;
  color: var(--color-text-muted) !important;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.file-icon {
  width: 40px;
  height: 40px;
  stroke: var(--color-accent);
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-details .file-name {
  display: block;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-details .file-size {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.remove-file {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 59, 48, 0.2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.remove-file:hover {
  background: rgba(255, 59, 48, 0.4);
}

.remove-file svg {
  width: 16px;
  height: 16px;
  stroke: var(--color-error);
}

.upload-tips {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: var(--spacing-md) 0 0;
  text-align: center;
}

/* Batch File List */
.batch-file-list {
  margin-top: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.batch-file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border-bottom: 1px solid var(--color-border);
}

.batch-files {
  max-height: 200px;
  overflow-y: auto;
}

.batch-file-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.batch-file-item:last-child {
  border-bottom: none;
}

.file-icon-sm {
  width: 20px;
  height: 20px;
  stroke: var(--color-accent);
  flex-shrink: 0;
}

.batch-file-item .file-name {
  flex: 1;
  font-size: var(--font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.batch-file-item .file-size {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.remove-file-sm {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
  transition: opacity var(--transition-fast);
}

.remove-file-sm:hover {
  opacity: 1;
}

.remove-file-sm svg {
  width: 14px;
  height: 14px;
  stroke: var(--color-error);
}

/* Batch Progress */
.batch-progress {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.progress-bar {
  height: 8px;
  background: var(--color-bg-dark);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.progress-items {
  margin-top: var(--spacing-md);
  max-height: 150px;
  overflow-y: auto;
}

.progress-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) 0;
  font-size: var(--font-size-sm);
  border-bottom: 1px solid var(--color-border);
}

.progress-item:last-child {
  border-bottom: none;
}

.progress-item .item-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: var(--spacing-md);
}

.progress-item .item-status {
  flex-shrink: 0;
}

.progress-item.pending .item-status {
  color: var(--color-text-muted);
}

.progress-item.uploading .item-status,
.progress-item.processing .item-status {
  color: var(--color-warning);
}

.progress-item.completed .item-status {
  color: var(--color-success);
}

.progress-item.failed .item-status {
  color: var(--color-error);
}
</style>
