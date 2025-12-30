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
          :class="['nav-item', { active: item.path === '/users' }]"
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
          <button class="back-btn" @click="goBack">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
            返回
          </button>
          <h1 class="page-title">用户详情</h1>
        </div>
      </header>

      <main class="content" v-if="user">
        <!-- 用户基本信息 -->
        <div class="card user-info-card">
          <div class="user-header">
            <div class="user-avatar">
              <img v-if="user.avatar_url" :src="user.avatar_url" alt="头像" />
              <div v-else class="avatar-placeholder">{{ user.email?.charAt(0).toUpperCase() }}</div>
            </div>
            <div class="user-meta">
              <h2 class="user-name">{{ user.nickname || user.email }}</h2>
              <p class="user-email">{{ user.email }}</p>
              <div class="user-badges">
                <span :class="['badge', `badge-${user.role}`]">{{ roleLabel(user.role) }}</span>
                <span :class="['badge', user.is_active ? 'badge-active' : 'badge-inactive']">
                  {{ user.is_active ? '正常' : '已禁用' }}
                </span>
                <span class="badge badge-plan">{{ user.subscription?.plan || 'free' }}</span>
              </div>
            </div>
          </div>
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-value">{{ user.stats?.voice_profiles || 0 }}</span>
              <span class="stat-label">声音档案</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ user.stats?.avatar_profiles || 0 }}</span>
              <span class="stat-label">头像档案</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ user.stats?.story_jobs || 0 }}</span>
              <span class="stat-label">故事生成</span>
            </div>
          </div>
          <div class="user-dates">
            <span>注册时间: {{ formatDate(user.created_at) }}</span>
            <span v-if="user.last_login_at">最后登录: {{ formatDate(user.last_login_at) }}</span>
          </div>
        </div>

        <!-- 标签页 -->
        <div class="tabs">
          <button
            :class="['tab', { active: activeTab === 'voice' }]"
            @click="activeTab = 'voice'"
          >
            声音档案 ({{ voiceProfiles.length }})
          </button>
          <button
            :class="['tab', { active: activeTab === 'avatar' }]"
            @click="activeTab = 'avatar'"
          >
            头像档案 ({{ avatarProfiles.length }})
          </button>
          <button
            :class="['tab', { active: activeTab === 'jobs' }]"
            @click="activeTab = 'jobs'"
          >
            故事生成记录 ({{ storyJobs.length }})
          </button>
        </div>

        <!-- 声音档案列表 -->
        <div class="card" v-if="activeTab === 'voice'">
          <div class="card-header">
            <h3>声音档案</h3>
          </div>
          <div v-if="voiceProfiles.length === 0" class="empty-state">
            暂无声音档案
          </div>
          <div v-else class="profile-grid">
            <div v-for="profile in voiceProfiles" :key="profile.id" class="profile-card">
              <div class="profile-icon voice-icon">
                <svg viewBox="0 0 24 24" width="32" height="32">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" fill="currentColor"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
              </div>
              <div class="profile-info">
                <h4>{{ profile.name }}</h4>
                <p class="profile-desc">{{ profile.description || '无描述' }}</p>
                <span class="profile-date">{{ formatDate(profile.created_at) }}</span>
              </div>
              <div class="profile-actions">
                <audio v-if="profile.reference_audio_url" :src="profile.reference_audio_url" controls class="audio-player"></audio>
                <button class="btn btn-danger btn-sm" @click="deleteVoiceProfile(profile.id)">删除</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 头像档案列表 -->
        <div class="card" v-if="activeTab === 'avatar'">
          <div class="card-header">
            <h3>头像档案</h3>
          </div>
          <div v-if="avatarProfiles.length === 0" class="empty-state">
            暂无头像档案
          </div>
          <div v-else class="profile-grid">
            <div v-for="profile in avatarProfiles" :key="profile.id" class="profile-card">
              <div class="profile-image">
                <img v-if="profile.image_url" :src="profile.image_url" alt="头像" />
                <div v-else class="image-placeholder">无图片</div>
              </div>
              <div class="profile-info">
                <h4>{{ profile.name }}</h4>
                <p class="profile-desc">{{ profile.description || '无描述' }}</p>
                <span class="profile-date">{{ formatDate(profile.created_at) }}</span>
              </div>
              <div class="profile-actions">
                <button class="btn btn-danger btn-sm" @click="deleteAvatarProfile(profile.id)">删除</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 故事生成记录 -->
        <div class="card" v-if="activeTab === 'jobs'">
          <div class="card-header">
            <h3>故事生成记录</h3>
          </div>
          <div v-if="storyJobs.length === 0" class="empty-state">
            暂无生成记录
          </div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>任务ID</th>
                <th>状态</th>
                <th>进度</th>
                <th>当前步骤</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in storyJobs" :key="job.id">
                <td class="job-id">{{ job.id?.slice(0, 8) }}...</td>
                <td>
                  <span :class="['status-badge', `status-${job.status}`]">
                    {{ statusLabel(job.status) }}
                  </span>
                </td>
                <td>{{ job.progress }}%</td>
                <td>{{ job.current_step || '-' }}</td>
                <td>{{ formatDate(job.created_at) }}</td>
                <td>
                  <a v-if="job.final_video_url" :href="getVideoUrl(job.final_video_url)" target="_blank" class="btn btn-primary btn-sm">
                    查看视频
                  </a>
                  <span v-else-if="job.error" class="error-text" :title="job.error">失败</span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <!-- 加载中 -->
      <div v-else class="loading">
        加载中...
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

const userId = route.params.id as string
const activeTab = ref('voice')

interface UserDetail {
  id: string
  email: string
  nickname: string | null
  avatar_url: string | null
  role: string
  subscription: { plan: string }
  is_active: boolean
  created_at: string
  last_login_at: string | null
  stats: {
    voice_profiles: number
    avatar_profiles: number
    story_jobs: number
  }
}

interface VoiceProfile {
  id: string
  name: string
  description: string | null
  reference_audio_url: string | null
  voice_id: string | null
  status: string
  created_at: string
}

interface AvatarProfile {
  id: string
  name: string
  description: string | null
  image_url: string | null
  status: string
  created_at: string
}

interface StoryJob {
  id: string
  story_id: string
  status: string
  progress: number
  current_step: string | null
  final_video_url: string | null
  error: string | null
  created_at: string
  completed_at: string | null
}

const user = ref<UserDetail | null>(null)
const voiceProfiles = ref<VoiceProfile[]>([])
const avatarProfiles = ref<AvatarProfile[]>([])
const storyJobs = ref<StoryJob[]>([])

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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    user: '普通用户',
    subscriber: '订阅用户',
    admin: '管理员'
  }
  return labels[role] || role
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

function getVideoUrl(url: string): string {
  if (url.startsWith('http')) return url
  if (url.startsWith('/files/')) return `http://112.124.70.81${url}`
  return url
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

function goBack() {
  router.push('/users')
}

async function fetchUserDetail() {
  try {
    const response = await api.get(`/admin/users/${userId}`)
    user.value = response.data.data
  } catch (error) {
    console.error('Failed to fetch user detail:', error)
  }
}

async function fetchVoiceProfiles() {
  try {
    const response = await api.get(`/admin/users/${userId}/voice-profiles`)
    voiceProfiles.value = response.data.data.items
  } catch (error) {
    console.error('Failed to fetch voice profiles:', error)
  }
}

async function fetchAvatarProfiles() {
  try {
    const response = await api.get(`/admin/users/${userId}/avatar-profiles`)
    avatarProfiles.value = response.data.data.items
  } catch (error) {
    console.error('Failed to fetch avatar profiles:', error)
  }
}

async function fetchStoryJobs() {
  try {
    const response = await api.get(`/admin/users/${userId}/story-jobs`)
    storyJobs.value = response.data.data.items
  } catch (error) {
    console.error('Failed to fetch story jobs:', error)
  }
}

async function deleteVoiceProfile(profileId: string) {
  if (!confirm('确定要删除此声音档案吗？')) return

  try {
    await api.delete(`/admin/users/${userId}/voice-profiles/${profileId}`)
    await fetchVoiceProfiles()
    await fetchUserDetail()
  } catch (error) {
    console.error('Failed to delete voice profile:', error)
  }
}

async function deleteAvatarProfile(profileId: string) {
  if (!confirm('确定要删除此头像档案吗？')) return

  try {
    await api.delete(`/admin/users/${userId}/avatar-profiles/${profileId}`)
    await fetchAvatarProfiles()
    await fetchUserDetail()
  } catch (error) {
    console.error('Failed to delete avatar profile:', error)
  }
}

onMounted(() => {
  fetchUserDetail()
  fetchVoiceProfiles()
  fetchAvatarProfiles()
  fetchStoryJobs()
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
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
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

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-secondary);
}

/* 用户信息卡片 */
.user-info-card {
  margin-bottom: var(--spacing-xl);
}

.user-header {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  font-size: var(--font-size-2xl);
  font-weight: 600;
}

.user-meta {
  flex: 1;
}

.user-name {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.user-email {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.user-badges {
  display: flex;
  gap: var(--spacing-sm);
}

.badge {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.badge-user {
  background: rgba(100, 100, 100, 0.2);
  color: #999;
}

.badge-subscriber {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.badge-admin {
  background: rgba(255, 149, 0, 0.2);
  color: var(--color-warning);
}

.badge-active {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.badge-inactive {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.badge-plan {
  background: rgba(0, 122, 255, 0.2);
  color: var(--color-info);
}

.user-stats {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--spacing-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--color-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.user-dates {
  display: flex;
  gap: var(--spacing-xl);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* 标签页 */
.tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.tab {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: var(--color-bg-dark-tertiary);
}

.tab.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* 卡片 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.card-header h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-muted);
}

/* 档案网格 */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.profile-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.profile-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  color: var(--color-primary);
}

.profile-image {
  width: 100%;
  height: 150px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg-dark-tertiary);
}

.profile-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.profile-info h4 {
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.profile-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.profile-date {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: auto;
}

.audio-player {
  width: 100%;
  height: 32px;
}

/* 表格 */
.job-id {
  font-family: monospace;
  font-size: var(--font-size-sm);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

.status-pending {
  background: rgba(100, 100, 100, 0.2);
  color: #999;
}

.status-processing {
  background: rgba(0, 122, 255, 0.2);
  color: var(--color-info);
}

.status-completed {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.status-failed {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.error-text {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  cursor: help;
}

.btn-danger {
  background: transparent;
  border: 1px solid var(--color-error);
  color: var(--color-error);
}

.btn-danger:hover {
  background: var(--color-error);
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: var(--font-size-sm);
}
</style>
