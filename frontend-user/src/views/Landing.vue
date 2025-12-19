<template>
  <div class="landing">
    <!-- 背景渐变 -->
    <div class="background-gradient"></div>

    <!-- 粒子效果 -->
    <div class="particles">
      <div v-for="i in 30" :key="i" class="particle" :style="getParticleStyle(i)"></div>
    </div>

    <!-- 主内容 -->
    <div class="landing-content">
      <!-- Logo 区域 - 带融合背景 -->
      <div class="logo-wrapper">
        <div class="logo-glow"></div>
        <div class="logo-container">
          <img src="/logo.png" alt="Echobot" class="logo" />
        </div>
      </div>

      <h1 class="brand-name">Echobot</h1>
      <p class="tagline">AI-Powered Digital Avatar Animation Platform</p>

      <!-- 进入按钮 -->
      <button class="enter-btn" @click="handleEnter">
        <span class="btn-text">Get Started</span>
        <span class="btn-arrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </span>
      </button>
    </div>

    <!-- 3D 轮播图区域 -->
    <div class="carousel-section" v-if="displayStories.length > 0">
      <div class="carousel-container">
        <div
          class="carousel-track"
          :style="{ transform: `rotateY(${carouselRotation}deg)` }"
        >
          <div
            v-for="(story, index) in displayStories"
            :key="story.id"
            class="carousel-item"
            :style="getCarouselItemStyle(index)"
          >
            <div class="card-inner">
              <img :src="story.thumbnail_url || getPlaceholderImage(index)" :alt="story.title" />
              <div class="card-overlay">
                <span class="card-title">{{ story.title }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 轮播指示器 -->
      <div class="carousel-indicators">
        <span
          v-for="(_, index) in displayStories"
          :key="index"
          :class="['indicator', { active: currentIndex === index }]"
          @click="goToSlide(index)"
        ></span>
      </div>
    </div>

    <!-- 无数据时的占位轮播 -->
    <div class="carousel-section" v-else>
      <div class="carousel-container">
        <div
          class="carousel-track"
          :style="{ transform: `rotateY(${carouselRotation}deg)` }"
        >
          <div
            v-for="index in 5"
            :key="index"
            class="carousel-item"
            :style="getCarouselItemStyle(index - 1)"
          >
            <div class="card-inner placeholder-card">
              <div class="placeholder-content">
                <div class="placeholder-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="2" width="20" height="20" rx="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <path d="M21 15l-5-5L5 21"/>
                  </svg>
                </div>
                <span class="placeholder-text">Amazing Stories</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const carouselRotation = ref(0)
let autoRotateInterval: number | null = null

const displayStories = computed(() => {
  return stories.value.slice(0, 5)
})

// 生成粒子样式
function getParticleStyle(index: number) {
  const size = Math.random() * 6 + 3
  const left = Math.random() * 100
  const animationDuration = Math.random() * 12 + 6
  const animationDelay = Math.random() * 5

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDuration: `${animationDuration}s`,
    animationDelay: `${animationDelay}s`
  }
}

// 获取轮播项样式
function getCarouselItemStyle(index: number) {
  const total = displayStories.value.length || 5
  const angle = (360 / total) * index
  const translateZ = 280

  return {
    transform: `rotateY(${angle}deg) translateZ(${translateZ}px)`
  }
}

// 获取占位图
function getPlaceholderImage(index: number) {
  const colors = ['#2D6B6B', '#3d7a7a', '#4d8a8a', '#5d9a9a', '#6daaaa']
  return `data:image/svg+xml,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180">
      <rect fill="${colors[index % colors.length]}" width="320" height="180"/>
      <text x="160" y="90" fill="#E8E4D4" font-size="14" text-anchor="middle" dominant-baseline="middle">Story ${index + 1}</text>
    </svg>
  `)}`
}

function goToSlide(index: number) {
  currentIndex.value = index
  const total = displayStories.value.length || 5
  carouselRotation.value = -(360 / total) * index
}

function autoRotate() {
  const total = displayStories.value.length || 5
  currentIndex.value = (currentIndex.value + 1) % total
  carouselRotation.value -= 360 / total
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
  // 自动轮播
  autoRotateInterval = window.setInterval(autoRotate, 4000)
})

onUnmounted(() => {
  if (autoRotateInterval) {
    clearInterval(autoRotateInterval)
  }
})
</script>

<style scoped>
.landing {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
}

/* 背景渐变 */
.background-gradient {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(45, 107, 107, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 50%, rgba(45, 107, 107, 0.1) 0%, transparent 40%),
    radial-gradient(ellipse at 20% 80%, rgba(45, 107, 107, 0.08) 0%, transparent 40%),
    linear-gradient(180deg, #0d0d0d 0%, #0a0a0a 100%);
  z-index: 0;
}

/* 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.particle {
  position: absolute;
  bottom: -10px;
  background: rgba(45, 107, 107, 0.8);
  border-radius: 50%;
  animation: float-up linear infinite;
  box-shadow: 0 0 10px rgba(45, 107, 107, 0.6);
}

@keyframes float-up {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) scale(0.3);
    opacity: 0;
  }
}

/* 主内容 */
.landing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
  margin-bottom: 60px;
}

/* Logo 包装器 */
.logo-wrapper {
  position: relative;
  margin-bottom: 24px;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(45, 107, 107, 0.7) 0%, rgba(45, 107, 107, 0.4) 40%, transparent 70%);
  border-radius: 50%;
  filter: blur(25px);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
}

.logo-container {
  width: 120px;
  height: 120px;
  border-radius: 28px;
  background: #23586a;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.3),
    0 0 80px rgba(35, 88, 106, 0.6),
    0 0 120px rgba(35, 88, 106, 0.35);
  position: relative;
  overflow: hidden;
}

.logo-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    rgba(45, 107, 107, 0.12) 60deg,
    transparent 120deg
  );
  animation: rotate-light 8s linear infinite;
}

@keyframes rotate-light {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo {
  width: 96px;
  height: 96px;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.brand-name {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
  margin-bottom: 8px;
  text-shadow: 0 2px 20px rgba(45, 107, 107, 0.3);
}

.tagline {
  font-size: 16px;
  color: rgba(232, 228, 212, 0.7);
  margin-bottom: 32px;
  letter-spacing: 4px;
}

/* 进入按钮 */
.enter-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 36px;
  background: linear-gradient(135deg, #2D6B6B 0%, #3d8080 100%);
  border: none;
  border-radius: 50px;
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow:
    0 4px 15px rgba(45, 107, 107, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.enter-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.enter-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 6px 25px rgba(45, 107, 107, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.enter-btn:hover::before {
  left: 100%;
}

.btn-arrow {
  display: flex;
  transition: transform 0.3s ease;
}

.enter-btn:hover .btn-arrow {
  transform: translateX(4px);
}

/* 轮播区域 */
.carousel-section {
  position: absolute;
  bottom: 40px;
  left: 0;
  right: 0;
  width: 100%;
  height: 220px;
  perspective: 1200px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.carousel-container {
  width: 100%;
  height: 180px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.carousel-track {
  width: 200px;
  height: 120px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.carousel-item {
  position: absolute;
  width: 200px;
  height: 120px;
  left: 0;
  top: 0;
  backface-visibility: hidden;
}

.card-inner {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card-inner:hover {
  transform: scale(1.05);
  box-shadow:
    0 15px 40px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.card-inner img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
}

.card-title {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

/* 占位卡片 */
.placeholder-card {
  background: linear-gradient(135deg, #1a2a2a 0%, #0d1a1a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.placeholder-icon {
  color: rgba(45, 107, 107, 0.5);
}

.placeholder-text {
  font-size: 12px;
  color: rgba(232, 228, 212, 0.4);
}

/* 轮播指示器 */
.carousel-indicators {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator.active {
  background: #2D6B6B;
  box-shadow: 0 0 10px rgba(45, 107, 107, 0.5);
}

.indicator:hover {
  background: rgba(45, 107, 107, 0.6);
}
</style>
