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
        <h1 class="page-title">费用统计</h1>
        <div class="admin-info">
          <span class="admin-name">{{ admin?.nickname || '管理员' }}</span>
          <span class="admin-role">{{ getRoleLabel(admin?.role) }}</span>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <!-- 日期筛选 -->
        <div class="filter-bar">
          <div class="filter-group">
            <label>开始日期</label>
            <input type="date" v-model="startDate" @change="fetchStatistics" />
          </div>
          <div class="filter-group">
            <label>结束日期</label>
            <input type="date" v-model="endDate" @change="fetchStatistics" />
          </div>
          <button class="btn-refresh" @click="fetchStatistics">刷新</button>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card total">
            <div class="stat-value">{{ formatCurrency(stats.total_cost) }}</div>
            <div class="stat-label">总费用</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ formatCurrency(stats.tts_cost) }}</div>
            <div class="stat-label">TTS 费用</div>
            <div class="stat-detail">{{ formatNumber(stats.tts_chars) }} 字符</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ formatCurrency(stats.emo_cost) }}</div>
            <div class="stat-label">EMO 数字人费用</div>
            <div class="stat-detail">{{ formatDuration(stats.emo_video_seconds) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.job_count }}</div>
            <div class="stat-label">完成任务数</div>
          </div>
        </div>

        <!-- 费用明细 -->
        <div class="section">
          <h2 class="section-title">费用明细</h2>
          <div class="detail-cards">
            <div class="detail-card">
              <div class="detail-header">
                <span class="detail-icon tts">T</span>
                <span class="detail-title">CosyVoice TTS</span>
              </div>
              <div class="detail-body">
                <div class="detail-row">
                  <span class="detail-label">处理字符数</span>
                  <span class="detail-value">{{ formatNumber(stats.tts_chars) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">单价</span>
                  <span class="detail-value">0.0002 元/字符</span>
                </div>
                <div class="detail-row total">
                  <span class="detail-label">费用</span>
                  <span class="detail-value">{{ formatCurrency(stats.tts_cost) }}</span>
                </div>
              </div>
            </div>
            <div class="detail-card">
              <div class="detail-header">
                <span class="detail-icon emo">E</span>
                <span class="detail-title">EMO 数字人</span>
              </div>
              <div class="detail-body">
                <div class="detail-row">
                  <span class="detail-label">人脸检测</span>
                  <span class="detail-value">{{ stats.emo_detect_count }} 次 ({{ formatCurrency(stats.emo_detect_cost) }})</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">视频生成</span>
                  <span class="detail-value">{{ formatDuration(stats.emo_video_seconds) }} ({{ formatCurrency(stats.emo_video_cost) }})</span>
                </div>
                <div class="detail-row total">
                  <span class="detail-label">费用</span>
                  <span class="detail-value">{{ formatCurrency(stats.emo_cost) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 任务列表 -->
        <div class="section">
          <h2 class="section-title">费用记录</h2>
          <div class="card">
            <table class="table">
              <thead>
                <tr>
                  <th>任务ID</th>
                  <th>用户</th>
                  <th>故事</th>
                  <th>模式</th>
                  <th>TTS费用</th>
                  <th>EMO费用</th>
                  <th>总费用</th>
                  <th>完成时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="job in jobs" :key="job.id">
                  <td class="job-id">{{ job.id.slice(-8) }}</td>
                  <td>{{ job.user?.nickname || job.user?.email || '-' }}</td>
                  <td class="story-title">{{ job.story?.title || '-' }}</td>
                  <td>
                    <span :class="['mode-badge', job.mode]">
                      {{ job.mode === 'dual' ? '双人' : '单人' }}
                    </span>
                  </td>
                  <td>{{ formatCurrency(job.tts_cost) }}</td>
                  <td>{{ formatCurrency(job.emo_detect_cost + job.emo_video_cost) }}</td>
                  <td class="total-cost">{{ formatCurrency(job.total_cost) }}</td>
                  <td>{{ formatDate(job.completed_at) }}</td>
                </tr>
                <tr v-if="jobs.length === 0">
                  <td colspan="8" class="empty">暂无费用记录</td>
                </tr>
              </tbody>
            </table>

            <!-- 分页 -->
            <div class="pagination" v-if="totalPages > 1">
              <button
                class="page-btn"
                :disabled="currentPage === 1"
                @click="goToPage(currentPage - 1)"
              >
                上一页
              </button>
              <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
              <button
                class="page-btn"
                :disabled="currentPage === totalPages"
                @click="goToPage(currentPage + 1)"
              >
                下一页
              </button>
            </div>
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

interface CostStats {
  total_cost: number
  tts_cost: number
  tts_chars: number
  emo_cost: number
  emo_detect_cost: number
  emo_detect_count: number
  emo_video_cost: number
  emo_video_seconds: number
  job_count: number
  daily_stats: { date: string; cost: number; jobs: number }[]
}

interface CostJob {
  id: string
  user: { id: string; email: string; nickname: string | null } | null
  story: { id: string; title: string } | null
  mode: string
  total_cost: number
  tts_cost: number
  tts_chars: number
  emo_detect_cost: number
  emo_video_cost: number
  emo_video_seconds: number
  created_at: string
  completed_at: string
}

const stats = ref<CostStats>({
  total_cost: 0,
  tts_cost: 0,
  tts_chars: 0,
  emo_cost: 0,
  emo_detect_cost: 0,
  emo_detect_count: 0,
  emo_video_cost: 0,
  emo_video_seconds: 0,
  job_count: 0,
  daily_stats: []
})

const jobs = ref<CostJob[]>([])
const startDate = ref('')
const endDate = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalJobs = ref(0)

const totalPages = computed(() => Math.ceil(totalJobs.value / pageSize.value))

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

function getRoleLabel(role: string | undefined): string {
  const labels: Record<string, string> = {
    user: '普通用户',
    subscriber: '订阅用户',
    admin: '管理员',
    super: '超级管理员'
  }
  return labels[role || ''] || role || '-'
}

function formatCurrency(amount: number | undefined): string {
  if (amount === undefined || amount === null) return '¥0.00'
  return `¥${amount.toFixed(4)}`
}

function formatNumber(num: number | undefined): string {
  if (num === undefined || num === null) return '0'
  return num.toLocaleString()
}

function formatDuration(seconds: number | undefined): string {
  if (!seconds) return '0秒'
  if (seconds < 60) return `${seconds.toFixed(1)}秒`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}分${secs}秒`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}

async function fetchStatistics() {
  try {
    const params: Record<string, string> = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await api.get('/admin/cost-statistics', { params })
    stats.value = response.data.data
  } catch (error) {
    console.error('Failed to fetch cost statistics:', error)
  }
}

async function fetchJobs() {
  try {
    const params: Record<string, string | number> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await api.get('/admin/cost-statistics/jobs', { params })
    jobs.value = response.data.data.items
    totalJobs.value = response.data.data.total
  } catch (error) {
    console.error('Failed to fetch cost jobs:', error)
  }
}

function goToPage(page: number) {
  currentPage.value = page
  fetchJobs()
}

onMounted(async () => {
  await adminStore.fetchProfile()
  await fetchStatistics()
  await fetchJobs()
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

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.filter-group label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.filter-group input[type="date"] {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border-dark);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.filter-group input[type="date"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
}

.btn-refresh {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-refresh:hover {
  background: var(--color-accent-light);
}

/* 统计卡片 */
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

.stat-card.total {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-light) 100%);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--color-accent-light);
  margin-bottom: var(--spacing-xs);
}

.stat-card.total .stat-value {
  color: white;
  font-size: var(--font-size-3xl);
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.stat-card.total .stat-label {
  color: rgba(255, 255, 255, 0.8);
}

.stat-detail {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  margin-top: var(--spacing-xs);
}

/* 费用明细 */
.section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-md);
}

.detail-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.detail-card {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-dark-tertiary);
}

.detail-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-weight: 600;
  color: white;
}

.detail-icon.tts {
  background: #3498db;
}

.detail-icon.emo {
  background: #e74c3c;
}

.detail-title {
  font-weight: 500;
}

.detail-body {
  padding: var(--spacing-lg);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-dark);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row.total {
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-dark);
  font-weight: 600;
}

.detail-label {
  color: var(--color-text-secondary);
}

.detail-value {
  color: var(--color-text-primary);
}

.detail-row.total .detail-value {
  color: var(--color-accent-light);
}

/* 任务表格 */
.job-id {
  font-family: monospace;
  color: var(--color-text-muted);
}

.story-title {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

.mode-badge.single {
  background: rgba(52, 152, 219, 0.2);
  color: #3498db;
}

.mode-badge.dual {
  background: rgba(155, 89, 182, 0.2);
  color: #9b59b6;
}

.total-cost {
  font-weight: 600;
  color: var(--color-accent-light);
}

.empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: var(--spacing-xl) !important;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border-dark);
}

.page-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border-dark);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-bg-dark-hover);
  border-color: var(--color-accent);
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
