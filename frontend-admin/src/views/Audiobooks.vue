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
          :class="['nav-item', { active: isActivePath(item.path) }]"
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
        <h1 class="page-title">有声书管理</h1>
        <div class="topbar-actions">
          <button class="btn btn-accent" @click="showCreateModal = true">
            新建故事
          </button>
        </div>
      </header>

      <main class="content">
        <!-- 故事列表 -->
        <div class="card">
          <table class="table">
            <thead>
              <tr>
                <th>标题</th>
                <th>语言</th>
                <th>分类</th>
                <th>年龄段</th>
                <th>预估时长</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="8" class="loading-cell">加载中...</td>
              </tr>
              <tr v-else-if="stories.length === 0">
                <td colspan="8" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="story in stories" :key="story.id">
                <td>
                  <div class="story-title-cell">
                    <img
                      v-if="story.thumbnail_url"
                      :src="story.thumbnail_url"
                      class="story-thumb"
                      :alt="story.title"
                    />
                    <span>{{ story.title }}</span>
                  </div>
                </td>
                <td>{{ getLanguageLabel(story.language) }}</td>
                <td>{{ getCategoryLabel(story.category) }}</td>
                <td>{{ story.age_group }}</td>
                <td>{{ formatDuration(story.estimated_duration) }}</td>
                <td>
                  <span :class="['status-badge', story.is_published ? 'active' : 'inactive']">
                    {{ story.is_published ? '已发布' : '未发布' }}
                  </span>
                </td>
                <td>{{ formatDate(story.created_at) }}</td>
                <td>
                  <div class="actions">
                    <button class="btn btn-outline btn-sm" @click="editStory(story)">
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

        <!-- 生成任务列表 -->
        <div class="card" style="margin-top: 24px;">
          <h2 class="card-title">用户生成记录</h2>
          <table class="table">
            <thead>
              <tr>
                <th>用户</th>
                <th>故事</th>
                <th>声音</th>
                <th>状态</th>
                <th>进度</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingJobs">
                <td colspan="6" class="loading-cell">加载中...</td>
              </tr>
              <tr v-else-if="jobs.length === 0">
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="job in jobs" :key="job.id">
                <td>{{ job.user_email || job.user_nickname || job.user_id }}</td>
                <td>{{ job.story_title }}</td>
                <td>{{ job.voice_name }}</td>
                <td>
                  <span :class="['status-badge', job.status]">
                    {{ getJobStatusLabel(job.status) }}
                  </span>
                </td>
                <td>
                  <div v-if="job.status === 'processing'" class="progress-mini">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: job.progress + '%' }"></div>
                    </div>
                    <span>{{ job.progress }}%</span>
                  </div>
                  <span v-else>{{ job.status === 'completed' ? '100%' : '-' }}</span>
                </td>
                <td>{{ formatDate(job.created_at) }}</td>
              </tr>
            </tbody>
          </table>

          <!-- 分页 -->
          <div class="pagination" v-if="jobsTotalPages > 1">
            <button
              class="page-btn"
              :disabled="jobsCurrentPage === 1"
              @click="changeJobsPage(jobsCurrentPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">{{ jobsCurrentPage }} / {{ jobsTotalPages }}</span>
            <button
              class="page-btn"
              :disabled="jobsCurrentPage === jobsTotalPages"
              @click="changeJobsPage(jobsCurrentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </main>
    </div>

    <!-- 创建/编辑故事弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal modal-lg">
        <h2 class="modal-title">{{ editingStory ? '编辑故事' : '新建故事' }}</h2>

        <form @submit.prevent="handleSaveStory">
          <div class="form-row">
            <div class="form-group">
              <label>中文标题 *</label>
              <input v-model="storyForm.title" type="text" class="input" required />
            </div>
            <div class="form-group">
              <label>英文标题 *</label>
              <input v-model="storyForm.title_en" type="text" class="input" required />
            </div>
          </div>

          <div class="form-group">
            <label>故事内容 *</label>
            <textarea
              v-model="storyForm.content"
              class="input textarea"
              rows="8"
              required
              placeholder="输入完整的故事内容..."
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>语言</label>
              <select v-model="storyForm.language" class="input">
                <option value="en">英文</option>
                <option value="zh">中文</option>
              </select>
            </div>
            <div class="form-group">
              <label>分类</label>
              <select v-model="storyForm.category" class="input">
                <option value="fairy_tale">童话故事</option>
                <option value="fable">寓言故事</option>
                <option value="adventure">冒险故事</option>
                <option value="bedtime">睡前故事</option>
              </select>
            </div>
            <div class="form-group">
              <label>年龄段</label>
              <select v-model="storyForm.age_group" class="input">
                <option value="3-5">3-5岁</option>
                <option value="5-8">5-8岁</option>
                <option value="8-12">8-12岁</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>封面图片URL</label>
              <input
                v-model="storyForm.thumbnail_url"
                type="text"
                class="input"
                placeholder="https://..."
              />
            </div>
            <div class="form-group">
              <label>背景音乐URL</label>
              <input
                v-model="storyForm.background_music_url"
                type="text"
                class="input"
                placeholder="https://..."
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>排序权重</label>
              <input v-model.number="storyForm.sort_order" type="number" class="input" />
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input v-model="storyForm.is_published" type="checkbox" />
                <span>立即发布</span>
              </label>
            </div>
          </div>

          <p v-if="saveError" class="error-msg">{{ saveError }}</p>

          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="closeCreateModal">
              取消
            </button>
            <button type="submit" class="btn btn-accent" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin'
import api from '../api'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()

interface AudiobookStory {
  id: string
  title: string
  title_en: string
  content: string
  language: string
  category: string
  age_group: string
  estimated_duration: number
  thumbnail_url: string | null
  background_music_url: string | null
  is_published: boolean
  sort_order: number
  created_at: string
}

interface AudiobookJob {
  id: string
  user_id: string
  user_email?: string
  user_nickname?: string
  story_title: string
  voice_name: string
  status: string
  progress: number
  current_step: string
  audio_url: string | null
  created_at: string
}

const stories = ref<AudiobookStory[]>([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20

const jobs = ref<AudiobookJob[]>([])
const loadingJobs = ref(false)
const jobsCurrentPage = ref(1)
const jobsTotalPages = ref(1)

const showCreateModal = ref(false)
const editingStory = ref<AudiobookStory | null>(null)
const saving = ref(false)
const saveError = ref('')

const storyForm = ref({
  title: '',
  title_en: '',
  content: '',
  language: 'en',
  category: 'fairy_tale',
  age_group: '5-8',
  thumbnail_url: '',
  background_music_url: '',
  is_published: true,
  sort_order: 0
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
  },
  {
    path: '/cost-statistics',
    name: '费用统计',
    icon: '<svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
  }
]

function isActivePath(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/')
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

function getLanguageLabel(lang: string): string {
  return lang === 'en' ? '英文' : '中文'
}

function getCategoryLabel(cat: string): string {
  const labels: Record<string, string> = {
    fairy_tale: '童话故事',
    fable: '寓言故事',
    adventure: '冒险故事',
    bedtime: '睡前故事'
  }
  return labels[cat] || cat
}

function getJobStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

function formatDuration(seconds: number): string {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

async function fetchStories() {
  loading.value = true
  try {
    const response = await api.get('/admin/audiobook/stories', {
      params: { page: currentPage.value, page_size: pageSize }
    })
    const data = response.data.data
    stories.value = data.items || []
    totalPages.value = Math.ceil((data.total || 0) / pageSize)
  } catch (error) {
    console.error('Failed to fetch audiobook stories:', error)
  } finally {
    loading.value = false
  }
}

async function fetchJobs() {
  loadingJobs.value = true
  try {
    const response = await api.get('/admin/audiobook/jobs', {
      params: { page: jobsCurrentPage.value, page_size: pageSize }
    })
    const data = response.data.data
    jobs.value = data.items || []
    jobsTotalPages.value = Math.ceil((data.total || 0) / pageSize)
  } catch (error) {
    console.error('Failed to fetch audiobook jobs:', error)
  } finally {
    loadingJobs.value = false
  }
}

function changePage(page: number) {
  currentPage.value = page
  fetchStories()
}

function changeJobsPage(page: number) {
  jobsCurrentPage.value = page
  fetchJobs()
}

function editStory(story: AudiobookStory) {
  editingStory.value = story
  storyForm.value = {
    title: story.title,
    title_en: story.title_en,
    content: story.content,
    language: story.language,
    category: story.category,
    age_group: story.age_group,
    thumbnail_url: story.thumbnail_url || '',
    background_music_url: story.background_music_url || '',
    is_published: story.is_published,
    sort_order: story.sort_order
  }
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
  editingStory.value = null
  saveError.value = ''
  storyForm.value = {
    title: '',
    title_en: '',
    content: '',
    language: 'en',
    category: 'fairy_tale',
    age_group: '5-8',
    thumbnail_url: '',
    background_music_url: '',
    is_published: true,
    sort_order: 0
  }
}

async function handleSaveStory() {
  saving.value = true
  saveError.value = ''

  try {
    const formData = new FormData()
    formData.append('title', storyForm.value.title)
    formData.append('title_en', storyForm.value.title_en)
    formData.append('content', storyForm.value.content)
    formData.append('language', storyForm.value.language)
    formData.append('category', storyForm.value.category)
    formData.append('age_group', storyForm.value.age_group)
    formData.append('is_published', String(storyForm.value.is_published))
    formData.append('sort_order', String(storyForm.value.sort_order))

    if (storyForm.value.thumbnail_url) {
      formData.append('thumbnail_url', storyForm.value.thumbnail_url)
    }
    if (storyForm.value.background_music_url) {
      formData.append('background_music_url', storyForm.value.background_music_url)
    }

    if (editingStory.value) {
      await api.put(`/admin/audiobook/stories/${editingStory.value.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      await api.post('/admin/audiobook/stories', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }

    closeCreateModal()
    await fetchStories()
  } catch (error: any) {
    console.error('Failed to save story:', error)
    saveError.value = error.response?.data?.detail || error.response?.data?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function handleDeleteStory(id: string) {
  if (!confirm('确定要删除此故事吗？此操作不可恢复。')) return

  try {
    await api.delete(`/admin/audiobook/stories/${id}`)
    await fetchStories()
  } catch (error) {
    console.error('Failed to delete story:', error)
  }
}

onMounted(() => {
  fetchStories()
  fetchJobs()
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width, 200px);
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
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  color: rgba(232, 228, 212, 0.85);
  text-decoration: none;
  transition: all var(--transition-fast);
  margin: 2px var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.nav-icon {
  width: 18px;
  height: 18px;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-btn {
  width: 100%;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
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
  gap: var(--spacing-md);
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

.card {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.table th {
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: var(--font-size-sm);
}

.loading-cell,
.empty-cell {
  text-align: center;
  color: var(--color-text-muted);
  padding: var(--spacing-xl) !important;
}

.story-title-cell {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.story-thumb {
  width: 60px;
  height: 36px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

.status-badge.active,
.status-badge.completed {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.status-badge.inactive,
.status-badge.failed {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.status-badge.pending {
  background: rgba(255, 149, 0, 0.2);
  color: var(--color-warning);
}

.status-badge.processing {
  background: rgba(0, 122, 255, 0.2);
  color: var(--color-info);
}

.actions {
  display: flex;
  gap: var(--spacing-sm);
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-sm {
  padding: 4px 8px;
  font-size: var(--font-size-sm);
}

.btn-accent {
  background: var(--color-accent, #2B5F6C);
  border: none;
  color: #fff;
}

.btn-accent:hover {
  opacity: 0.9;
}

.btn-accent:disabled {
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

.btn-danger {
  background: var(--color-error);
  border: none;
  color: #fff;
}

.btn-danger:hover {
  opacity: 0.9;
}

.progress-mini {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.progress-mini .progress-bar {
  flex: 1;
  max-width: 100px;
  height: 6px;
  background: var(--color-bg-dark);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-info);
  transition: width 0.3s ease;
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

.form-row {
  display: flex;
  gap: var(--spacing-md);
}

.form-row .form-group {
  flex: 1;
}

.input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
}

.input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.textarea {
  resize: vertical;
  min-height: 150px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding-top: 24px;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.error-msg {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-sm);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}
</style>
