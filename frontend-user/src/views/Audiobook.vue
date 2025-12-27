<template>
  <div class="page-layout">
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
      <header class="topbar">
        <h1 class="page-title">Audiobook</h1>
        <div class="user-menu" @click="toggleUserMenu">
          <img :src="user?.avatar_url || '/default-avatar.svg'" alt="avatar" class="user-avatar" />
          <span class="user-name">{{ user?.nickname || 'User' }}</span>
          <div v-if="showUserMenu" class="dropdown-menu">
            <a class="dropdown-item" @click="goToProfile">Profile</a>
            <a class="dropdown-item" @click="handleLogout">Sign Out</a>
          </div>
        </div>
      </header>

      <main class="content">
        <div class="audiobook-container">
          <!-- Coming Soon 提示 -->
          <div class="coming-soon">
            <div class="coming-soon-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                <path d="M8 7h8"/>
                <path d="M8 11h6"/>
                <path d="M8 15h4"/>
              </svg>
            </div>
            <h2 class="coming-soon-title">Audiobook Feature Coming Soon</h2>
            <p class="coming-soon-desc">
              Generate complete audiobooks with your cloned voice.
              Select from our library of stories and let your voice bring them to life.
            </p>

            <div class="feature-preview">
              <h3>Planned Features:</h3>
              <ul class="feature-list">
                <li>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span>Full-length story narration with cloned voice</span>
                </li>
                <li>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span>Multi-character voice support</span>
                </li>
                <li>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span>Digital avatar video overlay</span>
                </li>
                <li>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span>Synchronized lip movements</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const showUserMenu = ref(false)
const currentPath = ref('/audiobook')

const menuItems = [
  { path: '/dashboard', name: 'Story Library', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { path: '/upload-photo', name: 'Upload Photo', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>' },
  { path: '/upload-audio', name: 'Upload Audio', icon: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>' },
  { path: '/audiobook', name: 'Audiobook', icon: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 7h8"/><path d="M8 11h6"/>' },
  { path: '/generate', name: 'Generate Animation', icon: '<polygon points="5 3 19 12 5 21 5 3"/>' }
]

function navigate(path: string) {
  currentPath.value = path
  router.push(path)
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

onMounted(async () => {
  await userStore.fetchProfile()
})
</script>

<style scoped>
.page-layout {
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

/* Audiobook Container */
.audiobook-container {
  max-width: 800px;
  margin: 0 auto;
}

/* Coming Soon */
.coming-soon {
  background: var(--color-bg-dark-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  text-align: center;
}

.coming-soon-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--spacing-lg);
  background: rgba(43, 95, 108, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.coming-soon-icon svg {
  width: 40px;
  height: 40px;
  color: #2B5F6C;
}

.coming-soon-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.coming-soon-desc {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  max-width: 500px;
  margin: 0 auto var(--spacing-xl);
  line-height: 1.6;
}

.feature-preview {
  background: var(--color-bg-dark-tertiary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  text-align: left;
}

.feature-preview h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  color: var(--color-text-secondary);
}

.feature-list li svg {
  width: 20px;
  height: 20px;
  color: var(--color-success);
  flex-shrink: 0;
}
</style>
