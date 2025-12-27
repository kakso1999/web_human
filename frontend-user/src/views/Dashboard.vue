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
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="item.icon"></svg>
          <span class="nav-text">{{ item.name }}</span>
        </a>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">Sign Out</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <!-- 顶部栏 -->
      <header class="topbar">
        <h1 class="page-title">Story Library</h1>

        <div class="user-menu" @click="toggleUserMenu">
          <img
            :src="user?.avatar_url || '/default-avatar.svg'"
            alt="avatar"
            class="user-avatar"
          />
          <span class="user-name">{{ user?.nickname || 'User' }}</span>

          <div v-if="showUserMenu" class="dropdown-menu">
            <a class="dropdown-item" @click="goToProfile">Profile</a>
            <a class="dropdown-item" @click="handleLogout">Sign Out</a>
          </div>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <!-- 分类筛选器 -->
        <div class="category-filter">
          <button
            :class="['filter-btn', { active: selectedCategory === null }]"
            @click="selectCategory(null)"
          >
            All
          </button>
          <button
            v-for="cat in categories"
            :key="cat.id"
            :class="['filter-btn', { active: selectedCategory === cat.id }]"
            @click="selectCategory(cat.id)"
          >
            {{ cat.name_en || cat.name }}
          </button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <p>Loading...</p>
        </div>

        <!-- 按分类分组显示 -->
        <template v-else-if="selectedCategory === null">
          <div v-for="cat in categoriesWithStories" :key="cat.id" class="category-section">
            <h2 class="category-title">{{ cat.name_en || cat.name }}</h2>
            <div class="story-grid">
              <div
                v-for="story in cat.stories"
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
          </div>

          <!-- 无内容提示 -->
          <div v-if="categoriesWithStories.length === 0" class="empty-state">
            <p>No stories available</p>
          </div>
        </template>

        <!-- 单分类显示 -->
        <template v-else>
          <div class="category-section">
            <h2 class="category-title">{{ currentCategoryName }}</h2>
            <div class="story-grid">
              <div
                v-for="story in filteredStories"
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

            <!-- 无内容提示 -->
            <div v-if="filteredStories.length === 0" class="empty-state">
              <p>No stories in this category</p>
            </div>
          </div>
        </template>
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
const loading = ref(true)

interface Category {
  id: string
  name: string
  name_en: string
  story_count: number
}

interface Story {
  id: string
  title: string
  thumbnail_url: string | null
  duration: number
  category_id: string
}

interface CategoryWithStories extends Category {
  stories: Story[]
}

const categories = ref<Category[]>([])
const allStories = ref<Story[]>([])
const filteredStories = ref<Story[]>([])
const selectedCategory = ref<string | null>(null)

const menuItems = [
  { path: '/dashboard', name: 'Story Library', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { path: '/upload-photo', name: 'Upload Photo', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>' },
  { path: '/upload-audio', name: 'Upload Audio', icon: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>' },
  { path: '/audiobook', name: 'Audiobook', icon: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 7h8"/><path d="M8 11h6"/>' },
  { path: '/generate', name: 'Generate Animation', icon: '<polygon points="5 3 19 12 5 21 5 3"/>' }
]

// 按分类分组的故事
const categoriesWithStories = computed<CategoryWithStories[]>(() => {
  return categories.value
    .map(cat => ({
      ...cat,
      stories: allStories.value.filter(s => s.category_id === cat.id)
    }))
    .filter(cat => cat.stories.length > 0)
})

// 当前选中分类的名称
const currentCategoryName = computed(() => {
  if (!selectedCategory.value) return 'All'
  const cat = categories.value.find(c => c.id === selectedCategory.value)
  return cat ? (cat.name_en || cat.name) : ''
})

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function navigate(path: string) {
  currentPath.value = path
  if (path !== '/dashboard') {
    router.push(path)
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

async function fetchCategories() {
  try {
    const response = await api.get('/stories/categories')
    categories.value = response.data.data || []
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

async function fetchAllStories() {
  try {
    // 获取所有故事（较大的page_size）
    const response = await api.get('/stories', {
      params: { page: 1, page_size: 100 }
    })
    allStories.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  }
}

async function fetchStoriesByCategory(categoryId: string) {
  try {
    const response = await api.get('/stories', {
      params: { category_id: categoryId, page: 1, page_size: 100 }
    })
    filteredStories.value = response.data.data?.items || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  }
}

async function selectCategory(categoryId: string | null) {
  selectedCategory.value = categoryId

  if (categoryId === null) {
    // 显示全部，使用已加载的数据
    filteredStories.value = []
  } else {
    // 按分类筛选
    loading.value = true
    await fetchStoriesByCategory(categoryId)
    loading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  await userStore.fetchProfile()
  await Promise.all([fetchCategories(), fetchAllStories()])
  loading.value = false
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
  flex-shrink: 0;
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
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  color: rgba(232, 228, 212, 0.85);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin: 2px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border-left-color: #E8E4D4;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
  margin-top: auto;
}

.logout-btn {
  width: 100%;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: var(--font-size-sm);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
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
  z-index: 100;
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

/* 分类筛选器 */
.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.filter-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background: var(--color-bg-dark-hover);
  color: var(--color-text-primary);
}

.filter-btn.active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: white;
}

/* 分类区块 */
.category-section {
  margin-bottom: var(--spacing-2xl);
}

.category-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--color-accent);
  display: inline-block;
}

/* 故事网格 */
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

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-3xl);
  color: var(--color-text-muted);
}

.loading-state p,
.empty-state p {
  font-size: var(--font-size-lg);
}
</style>
