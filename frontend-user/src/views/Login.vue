<template>
  <div class="auth-page">
    <!-- 背景效果 -->
    <div class="background-gradient"></div>
    <div class="particles">
      <div v-for="i in 25" :key="i" class="particle" :style="getParticleStyle(i)"></div>
    </div>

    <div class="auth-container">
      <!-- Logo 区域 - 带融合背景 -->
      <div class="logo-wrapper">
        <div class="logo-glow"></div>
        <div class="logo-container">
          <img src="/logo.png" alt="Echobot" class="logo" />
        </div>
      </div>

      <h1 class="auth-title">登录</h1>
      <p class="auth-subtitle">欢迎回来，继续探索精彩故事</p>

      <!-- 登录表单 -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <input
              v-model="email"
              type="email"
              class="input"
              placeholder="邮箱地址"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
            <input
              v-model="password"
              type="password"
              class="input"
              placeholder="密码"
              required
            />
          </div>
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span class="btn-text">{{ loading ? '登录中...' : '登录' }}</span>
          <span class="btn-arrow" v-if="!loading">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </span>
        </button>
      </form>

      <!-- 分隔线 -->
      <div class="divider">
        <span>或</span>
      </div>

      <!-- Google 登录 -->
      <button class="google-btn" @click="handleGoogleLogin">
        <svg class="google-icon" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        使用 Google 账号登录
      </button>

      <!-- 注册链接 -->
      <p class="auth-link">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function getParticleStyle(index: number) {
  const size = Math.random() * 5 + 2
  const left = Math.random() * 100
  const animationDuration = Math.random() * 12 + 6
  const animationDelay = Math.random() * 6

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDuration: `${animationDuration}s`,
    animationDelay: `${animationDelay}s`
  }
}

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    await userStore.login(email.value, password.value)

    const redirect = route.query.redirect as string || '/dashboard'
    router.push(redirect)
  } catch (err: any) {
    error.value = err.response?.data?.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}

function handleGoogleLogin() {
  window.location.href = 'http://localhost:8000/api/v1/auth/google/url'
}
</script>

<style scoped>
.auth-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
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
    radial-gradient(ellipse at 50% 0%, rgba(45, 107, 107, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(45, 107, 107, 0.08) 0%, transparent 40%),
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
  box-shadow: 0 0 8px rgba(45, 107, 107, 0.6);
}

@keyframes float-up {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 0.9;
  }
  90% {
    opacity: 0.9;
  }
  100% {
    transform: translateY(-100vh) scale(0.3);
    opacity: 0;
  }
}

.auth-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 10;
}

/* Logo 包装器 */
.logo-wrapper {
  position: relative;
  margin-bottom: 8px;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(45, 107, 107, 0.6) 0%, rgba(45, 107, 107, 0.3) 40%, transparent 70%);
  border-radius: 50%;
  filter: blur(20px);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
}

.logo-container {
  width: 88px;
  height: 88px;
  border-radius: 22px;
  background: #23586a;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 50px rgba(35, 88, 106, 0.5),
    0 0 80px rgba(35, 88, 106, 0.3);
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
    rgba(45, 107, 107, 0.15) 60deg,
    transparent 120deg
  );
  animation: rotate-light 8s linear infinite;
}

@keyframes rotate-light {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo {
  width: 68px;
  height: 68px;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.auth-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  margin: 0;
}

.auth-subtitle {
  font-size: 14px;
  color: rgba(232, 228, 212, 0.6);
  margin: 0 0 8px 0;
}

.auth-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  width: 100%;
}

.input-wrapper {
  position: relative;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: rgba(232, 228, 212, 0.4);
  pointer-events: none;
}

.input {
  width: 100%;
  padding: 14px 16px 14px 48px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  transition: all 0.3s ease;
}

.input::placeholder {
  color: rgba(232, 228, 212, 0.4);
}

.input:focus {
  outline: none;
  border-color: rgba(45, 107, 107, 0.6);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(45, 107, 107, 0.1);
}

.error-message {
  color: #ff6b6b;
  font-size: 13px;
  text-align: center;
  padding: 8px 12px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 8px;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, #2D6B6B 0%, #3d8080 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow:
    0 4px 15px rgba(45, 107, 107, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  transition: left 0.5s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 6px 20px rgba(45, 107, 107, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.submit-btn:hover:not(:disabled)::before {
  left: 100%;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-arrow {
  display: flex;
  transition: transform 0.3s ease;
}

.submit-btn:hover:not(:disabled) .btn-arrow {
  transform: translateX(4px);
}

.divider {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
  color: rgba(232, 228, 212, 0.4);
  font-size: 13px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
}

.google-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.google-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.google-icon {
  width: 20px;
  height: 20px;
}

.auth-link {
  color: rgba(232, 228, 212, 0.6);
  font-size: 14px;
  margin: 0;
}

.auth-link a {
  color: #4d9a9a;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s ease;
}

.auth-link a:hover {
  color: #6daaaa;
  text-decoration: underline;
}
</style>
