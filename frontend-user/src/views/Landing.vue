<template>
  <div class="landing">
    <!-- 背景粒子效果 -->
    <div class="background-particles"></div>

    <!-- 主内容 -->
    <div class="landing-content">
      <!-- Logo 和标语 -->
      <div class="logo-section">
        <img src="/logo.png" alt="Echobot" class="logo" />
        <h1 class="tagline">AI驱动的数字人动画平台</h1>
      </div>

      <!-- 进入按钮 -->
      <button class="enter-btn" @click="handleEnter">
        点击进入
        <span class="arrow">→</span>
      </button>
    </div>

    <!-- 底部轮播图 -->
    <div class="carousel-section" v-if="stories.length > 0">
      <div class="carousel-3d">
        <div
          v-for="(story, index) in displayStories"
          :key="story.id"
          class="carousel-item"
          :style="getItemStyle(index)"
        >
          <img :src="story.thumbnail_url || '/placeholder.svg'" :alt="story.title" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()

interface Story {
  id: string
  title: string
  thumbnail_url: string | null
}

const stories = ref<Story[]>([])
const currentIndex = ref(0)

const displayStories = computed(() => {
  if (stories.value.length === 0) return []
  // 显示5个故事用于轮播
  return stories.value.slice(0, 5)
})

function getItemStyle(index: number) {
  const total = displayStories.value.length
  const angle = (360 / total) * index
  const translateZ = 250

  return {
    transform: `rotateY(${angle}deg) translateZ(${translateZ}px)`
  }
}

function handleEnter() {
  const token = localStorage.getItem('access_token')
  if (token) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}

async function fetchRandomStories() {
  try {
    const response = await api.get('/stories/random?limit=10')
    stories.value = response.data.data || []
  } catch (error) {
    console.error('Failed to fetch stories:', error)
  }
}

onMounted(() => {
  fetchRandomStories()
})
</script>

<style scoped>
.landing {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.background-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(ellipse at center, #1a1a2e 0%, #0d0d0d 100%);
  z-index: -1;
}

.landing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xl);
  z-index: 1;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.logo {
  width: 120px;
  height: auto;
}

.tagline {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  font-weight: 400;
}

.enter-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-2xl);
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-full);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.enter-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.arrow {
  transition: transform var(--transition-normal);
}

.enter-btn:hover .arrow {
  transform: translateX(4px);
}

.carousel-section {
  position: absolute;
  bottom: 80px;
  width: 100%;
  height: 200px;
  perspective: 1000px;
}

.carousel-3d {
  width: 300px;
  height: 180px;
  position: relative;
  margin: 0 auto;
  transform-style: preserve-3d;
  animation: rotate 20s infinite linear;
}

.carousel-item {
  position: absolute;
  width: 200px;
  height: 120px;
  left: 50px;
  top: 30px;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.carousel-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@keyframes rotate {
  from {
    transform: rotateY(0deg);
  }
  to {
    transform: rotateY(360deg);
  }
}
</style>
