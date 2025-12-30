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
      <!-- 顶部栏 -->
      <header class="topbar">
        <h1 class="page-title">仪表盘</h1>
        <div class="admin-info">
          <span class="admin-name">{{ admin?.nickname || '管理员' }}</span>
          <span class="admin-role">{{ getRoleLabel(admin?.role) }}</span>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalUsers }}</div>
            <div class="stat-label">总用户数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalStories }}</div>
            <div class="stat-label">总故事数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.activeSubscribers }}</div>
            <div class="stat-label">活跃订阅</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ formatRevenue(stats.monthlyRevenue) }}</div>
            <div class="stat-label">月收入</div>
          </div>
        </div>

        <!-- 最近用户 -->
        <div class="section">
          <h2 class="section-title">最近注册用户</h2>
          <div class="card">
            <table class="table">
              <thead>
                <tr>
                  <th>邮箱</th>
                  <th>昵称</th>
                  <th>角色</th>
                  <th>注册时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in recentUsers" :key="user.id">
                  <td>{{ user.email }}</td>
                  <td>{{ user.nickname || '-' }}</td>
                  <td>{{ getRoleLabel(user.role) }}</td>
                  <td>{{ formatDate(user.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 最近故事 -->
        <div class="section">
          <h2 class="section-title">最近上传故事</h2>
          <div class="card">
            <table class="table">
              <thead>
                <tr>
                  <th>标题</th>
                  <th>时长</th>
                  <th>状态</th>
                  <th>创建时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="story in recentStories" :key="story.id">
                  <td>{{ story.title }}</td>
                  <td>{{ formatDuration(story.duration) }}</td>
                  <td>
                    <span :class="['status-badge', story.status]">
                      {{ getStatusLabel(story.status) }}
                    </span>
                  </td>
                  <td>{{ formatDate(story.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
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

const admin = computed(() => adminStore.user)
const currentPath = computed(() => route.path)

interface Stats {
  totalUsers: number
  totalStories: number
  activeSubscribers: number
  monthlyRevenue: number
}

interface User {
  id: string
  email: string
  nickname: string | null
  role: string
  created_at: string
}

interface Story {
  id: string
  title: string
  duration: number
  status: string
  created_at: string
}

const stats = ref<Stats>({
  totalUsers: 0,
  totalStories: 0,
  activeSubscribers: 0,
  monthlyRevenue: 0
})

const recentUsers = ref<User[]>([])
const recentStories = ref<Story[]>([])

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

function getRoleLabel(role: string | undefined): string {
  const labels: Record<string, string> = {
    user: '普通用户',
    subscriber: '订阅用户',
    admin: '管理员',
    super: '超级管理员'
  }
  return labels[role || ''] || role || '-'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: '正常',
    inactive: '已下架',
    processing: '处理中'
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

function formatRevenue(amount: number): string {
  return `¥${amount.toLocaleString()}`
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

async function fetchDashboard() {
  try {
    const response = await api.get('/admin/dashboard')
    const data = response.data.data

    stats.value = {
      totalUsers: data.total_users,
      totalStories: data.total_stories,
      activeSubscribers: data.active_subscribers,
      monthlyRevenue: data.monthly_revenue
    }

    recentUsers.value = data.recent_users || []
    recentStories.value = data.recent_stories || []
  } catch (error) {
    console.error('Failed to fetch dashboard:', error)
  }
}

onMounted(async () => {
  await adminStore.fetchProfile()
  await fetchDashboard()
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

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
}

.admin-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.admin-name {
  color: var(--color-text-primary);
  font-weight: 500;
}

.admin-role {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.stat-card {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  text-align: center;
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: 600;
  color: var(--color-accent-light);
  margin-bottom: var(--spacing-xs);
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-md);
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
</style>
