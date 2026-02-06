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
        <!-- 概览卡片 -->
        <div class="overview-grid">
          <div class="overview-card revenue-overview">
            <div class="overview-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z"/>
              </svg>
            </div>
            <div class="overview-content">
              <div class="overview-value">${{ revenue.total_revenue?.toFixed(2) || '0.00' }}</div>
              <div class="overview-label">总收入</div>
            </div>
          </div>
          <div class="overview-card cost-overview">
            <div class="overview-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>
              </svg>
            </div>
            <div class="overview-content">
              <div class="overview-value">{{ formatCurrency(stats.total_cost) }}</div>
              <div class="overview-label">总支出</div>
            </div>
          </div>
          <div class="overview-card profit-overview" :class="{ positive: netProfitCNY > 0, negative: netProfitCNY < 0 }">
            <div class="overview-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
              </svg>
            </div>
            <div class="overview-content">
              <div class="overview-value">{{ netProfitCNY >= 0 ? '+' : '' }}{{ formatCurrency(Math.abs(netProfitCNY)) }}</div>
              <div class="overview-label">净利润 (汇率 7.2)</div>
            </div>
          </div>
        </div>

        <!-- Tab 切换 -->
        <div class="tabs">
          <button :class="['tab', { active: activeTab === 'revenue' }]" @click="activeTab = 'revenue'">
            收入明细
          </button>
          <button :class="['tab', { active: activeTab === 'cost' }]" @click="activeTab = 'cost'">
            支出明细
          </button>
        </div>

        <!-- 日期筛选 -->
        <div class="filter-bar">
          <div class="filter-group">
            <label>开始日期</label>
            <input type="date" v-model="startDate" @change="refreshAll" />
          </div>
          <div class="filter-group">
            <label>结束日期</label>
            <input type="date" v-model="endDate" @change="refreshAll" />
          </div>
          <button class="btn-refresh" @click="refreshAll">刷新</button>
        </div>

        <!-- 收入 Tab -->
        <div v-if="activeTab === 'revenue'">
          <div class="stats-grid stats-grid-4">
            <div class="stat-card revenue">
              <div class="stat-value">${{ revenue.total_revenue?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">总收入</div>
              <div class="stat-detail">{{ revenue.completed_orders || 0 }} 笔订单</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${{ revenue.basic_revenue?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">Basic 订阅</div>
              <div class="stat-detail">{{ revenue.basic_orders || 0 }} 笔 × $9.90</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${{ revenue.premium_revenue?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">Premium 订阅</div>
              <div class="stat-detail">{{ revenue.premium_orders || 0 }} 笔 × $19.90</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ revenue.completed_orders || 0 }}</div>
              <div class="stat-label">完成订单数</div>
              <div class="stat-detail">成功支付</div>
            </div>
          </div>

          <!-- 收入订单列表 -->
          <div class="section">
            <h2 class="section-title">支付订单</h2>
            <div class="card">
              <table class="table">
                <thead>
                  <tr>
                    <th>订单号</th>
                    <th>用户</th>
                    <th>计划</th>
                    <th>金额</th>
                    <th>状态</th>
                    <th>付款邮箱</th>
                    <th>时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="order in revenueOrders" :key="order.order_id">
                    <td class="order-id">{{ order.order_id.slice(-12) }}</td>
                    <td>{{ order.user?.nickname || order.user?.email || '-' }}</td>
                    <td>
                      <span :class="['plan-badge', order.plan]">{{ order.plan }}</span>
                    </td>
                    <td class="amount">${{ order.amount?.toFixed(2) }}</td>
                    <td>
                      <span :class="['status-badge', order.status.toLowerCase()]">
                        {{ order.status === 'COMPLETED' ? '已完成' : '待支付' }}
                      </span>
                    </td>
                    <td>{{ order.payer_email || '-' }}</td>
                    <td>{{ formatDate(order.completed_at || order.created_at) }}</td>
                  </tr>
                  <tr v-if="revenueOrders.length === 0">
                    <td colspan="7" class="empty">暂无支付订单</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 支出 Tab -->
        <div v-if="activeTab === 'cost'">
          <div class="stats-grid stats-grid-4">
            <div class="stat-card total">
              <div class="stat-value">{{ formatCurrency(stats.total_cost) }}</div>
              <div class="stat-label">总支出 (AI成本)</div>
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

interface RevenueStats {
  total_revenue: number
  completed_orders: number
  basic_revenue: number
  basic_orders: number
  premium_revenue: number
  premium_orders: number
  daily_stats: { date: string; revenue: number; orders: number }[]
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

const revenue = ref<RevenueStats>({
  total_revenue: 0,
  completed_orders: 0,
  basic_revenue: 0,
  basic_orders: 0,
  premium_revenue: 0,
  premium_orders: 0,
  daily_stats: []
})

const netProfitCNY = computed(() => {
  // 收入是美元，成本是人民币，按汇率7.2换算
  const revenueInCNY = revenue.value.total_revenue * 7.2
  return revenueInCNY - stats.value.total_cost
})

const activeTab = ref<'revenue' | 'cost'>('revenue')
const jobs = ref<CostJob[]>([])
const revenueOrders = ref<any[]>([])
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

async function fetchRevenue() {
  try {
    const params: Record<string, string> = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await api.get('/admin/revenue-statistics', { params })
    revenue.value = response.data.data
  } catch (error) {
    console.error('Failed to fetch revenue statistics:', error)
  }
}

async function fetchRevenueOrders() {
  try {
    const params: Record<string, string | number> = {
      page: 1,
      page_size: 50
    }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await api.get('/admin/revenue-statistics/orders', { params })
    revenueOrders.value = response.data.data.items
  } catch (error) {
    console.error('Failed to fetch revenue orders:', error)
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

async function refreshAll() {
  await Promise.all([
    fetchStatistics(),
    fetchRevenue(),
    fetchRevenueOrders(),
    fetchJobs()
  ])
}

onMounted(async () => {
  await adminStore.fetchProfile()
  await refreshAll()
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

/* Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.overview-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
}

.overview-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-bg-dark-tertiary);
  color: var(--color-text-secondary);
}

.overview-card.revenue-overview .overview-icon {
  background: rgba(39, 174, 96, 0.15);
  color: #27ae60;
}

.overview-card.cost-overview .overview-icon {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.overview-card.profit-overview .overview-icon {
  background: rgba(52, 152, 219, 0.15);
  color: #3498db;
}

.overview-card.profit-overview.positive .overview-icon {
  background: rgba(39, 174, 96, 0.15);
  color: #27ae60;
}

.overview-card.profit-overview.negative .overview-icon {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.overview-content {
  flex: 1;
}

.overview-value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.overview-card.revenue-overview .overview-value {
  color: #27ae60;
}

.overview-card.cost-overview .overview-value {
  color: #e74c3c;
}

.overview-card.profit-overview.positive .overview-value {
  color: #27ae60;
}

.overview-card.profit-overview.negative .overview-value {
  color: #e74c3c;
}

.overview-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
}

/* Tabs */
.tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-xs);
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  width: fit-content;
}

.tab {
  padding: var(--spacing-sm) var(--spacing-xl);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab:hover {
  color: var(--color-text-primary);
}

.tab.active {
  background: var(--color-accent);
  color: white;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.stats-grid-4 {
  grid-template-columns: repeat(4, 1fr);
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

.stat-card.revenue {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
}

.stat-card.revenue .stat-value {
  color: white;
  font-size: var(--font-size-3xl);
}

.stat-card.revenue .stat-label {
  color: rgba(255, 255, 255, 0.8);
}

.stat-card.revenue .stat-detail {
  color: rgba(255, 255, 255, 0.6);
}

.stat-card.profit .stat-value.positive {
  color: #2ecc71;
}

.stat-card.profit .stat-value.negative {
  color: #e74c3c;
}

.revenue-grid {
  margin-bottom: var(--spacing-lg);
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

/* 订单表格样式 */
.order-id {
  font-family: monospace;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.amount {
  color: #27ae60;
  font-weight: 600;
}

.plan-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: capitalize;
}

.plan-badge.basic {
  background: rgba(52, 152, 219, 0.2);
  color: #3498db;
}

.plan-badge.premium {
  background: rgba(155, 89, 182, 0.2);
  color: #9b59b6;
}

.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.status-badge.completed {
  background: rgba(39, 174, 96, 0.2);
  color: #27ae60;
}

.status-badge.created,
.status-badge.pending {
  background: rgba(241, 196, 15, 0.2);
  color: #f1c40f;
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
