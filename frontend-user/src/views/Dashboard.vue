<template>
  <div class="dashboard-layout">
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
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.name }}</span>
        </a>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <!-- 顶部栏 -->
      <header class="topbar">
        <h1 class="page-title">故事库管理</h1>

        <div class="user-menu" @click="toggleUserMenu">
          <img
            :src="user?.avatar_url || '/default-avatar.svg'"
            alt="avatar"
            class="user-avatar"
          />
          <span class="user-name">{{ user?.nickname || '用户' }}</span>

          <div v-if="showUserMenu" class="dropdown-menu">
            <a class="dropdown-item" @click="goToProfile">个人信息</a>
            <a class="dropdown-item" @click="handleLogout">退出登录</a>
          </div>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <p class="content-desc">管理您的原始动画故事库</p>

        <!-- 故事卡片网格 -->
        <div class="story-grid">
          <div
            v-for="story in stories"
            :key="story.id"
            class="story-card"
            @click="goToStory(story.id)"
          >
            <div class="story-thumbnail">
              <img :src="story.thumbnail_url || '/placeholder.svg'" :alt="story.title" />
              <span class="story-duration">{{ formatDuration(story.duration) }}</span>
            </div>
            <div class="story-info">
              <h3 class="story-title">{{ story.title }}</h3>
            </div>
          </div>
        </div>

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
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const showUserMenu = ref(false)
const currentPath = ref('/dashboard')

interface Story {
  id: string
  title: string
  thumbnail_url: string | null
  duration: number
}

const stories = ref<Story[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20

const menuItems = [
  { path: '/dashboard', name: '故事库管理', icon: '田' },
  { path: '/upload-photo', name: '上传照片', icon: '图' },
  { path: '/upload-audio', name: '上传音频', icon: '音' },
  { path: '/generate', name: '生成动画', icon: '播' }
]

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function navigate(path: string) {
  currentPath.value = path
  if (path === '/dashboard') {
    // 当前页面
  } else {
    // TODO: 其他页面
  }
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

function goToStory(id: string) {
  router.push(`/story/${id}`)
}

async function fetchStories() {
  try {
    const response = await api.get('/stories', {
      params: { page: currentPage.value, page_size: pageSize }
    })
    const data = response.data.data
    stories.value = data.items
    totalPages.value = Math.ceil(data.total / pageSize)
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  }
}

function changePage(page: number) {
  currentPage.value = page
  fetchStories()
}

onMounted(async () => {
  await userStore.fetchProfile()
  await fetchStories()
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  width: 100%;
  height: 100vh;
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
  padding: var(--spacing-md) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  color: var(--color-text-secondary);
  cursor: pointer;
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

.content-desc {
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-xl);
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--spacing-lg);
}

.story-card {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--transition-normal);
}

.story-card:hover {
  transform: translateY(-4px);
}

.story-thumbnail {
  position: relative;
  aspect-ratio: 16 / 9;
}

.story-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.story-duration {
  position: absolute;
  bottom: var(--spacing-sm);
  right: var(--spacing-sm);
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
}

.story-info {
  padding: var(--spacing-md);
}

.story-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
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
