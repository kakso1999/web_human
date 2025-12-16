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
        <h1 class="page-title">用户管理</h1>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            class="input search-input"
            placeholder="搜索用户邮箱或昵称"
            @input="handleSearch"
          />
        </div>
      </header>

      <main class="content">
        <div class="card">
          <table class="table">
            <thead>
              <tr>
                <th>邮箱</th>
                <th>昵称</th>
                <th>角色</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.email }}</td>
                <td>{{ user.nickname || '-' }}</td>
                <td>
                  <select
                    :value="user.role"
                    class="role-select"
                    @change="handleRoleChange(user.id, ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="user">普通用户</option>
                    <option value="subscriber">订阅用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </td>
                <td>
                  <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                    {{ user.is_active ? '正常' : '已禁用' }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <div class="actions">
                    <button
                      v-if="user.is_active"
                      class="btn btn-outline btn-sm"
                      @click="handleDisableUser(user.id)"
                    >
                      禁用
                    </button>
                    <button
                      v-else
                      class="btn btn-primary btn-sm"
                      @click="handleEnableUser(user.id)"
                    >
                      启用
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

const currentPath = computed(() => route.path)

interface User {
  id: string
  email: string
  nickname: string | null
  role: string
  is_active: boolean
  created_at: string
}

const users = ref<User[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20
const searchQuery = ref('')
let searchTimeout: number | null = null

const menuItems = [
  { path: '/dashboard', name: '仪表盘', icon: '仪' },
  { path: '/users', name: '用户管理', icon: '用' },
  { path: '/stories', name: '故事管理', icon: '事' }
]

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
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
    fetchUsers()
  }, 300)
}

async function fetchUsers() {
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await api.get('/admin/users', { params })
    const data = response.data.data

    users.value = data.items
    totalPages.value = Math.ceil(data.total / pageSize)
  } catch (error) {
    console.error('Failed to fetch users:', error)
  }
}

function changePage(page: number) {
  currentPage.value = page
  fetchUsers()
}

async function handleRoleChange(userId: string, role: string) {
  try {
    await api.put(`/admin/users/${userId}/role`, { role })
    await fetchUsers()
  } catch (error) {
    console.error('Failed to change role:', error)
  }
}

async function handleDisableUser(userId: string) {
  if (!confirm('确定要禁用此用户吗？')) return

  try {
    await api.put(`/admin/users/${userId}/status`, { is_active: false })
    await fetchUsers()
  } catch (error) {
    console.error('Failed to disable user:', error)
  }
}

async function handleEnableUser(userId: string) {
  try {
    await api.put(`/admin/users/${userId}/status`, { is_active: true })
    await fetchUsers()
  } catch (error) {
    console.error('Failed to enable user:', error)
  }
}

onMounted(() => {
  fetchUsers()
})
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

.search-box {
  width: 300px;
}

.search-input {
  padding: var(--spacing-sm) var(--spacing-md);
}

.content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}

.role-select {
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  padding: 4px 8px;
  cursor: pointer;
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
</style>
