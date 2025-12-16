<template>
  <div class="login-page">
    <!-- 背景效果 -->
    <div class="background-gradient"></div>
    <div class="grid-pattern"></div>
    <div class="particles">
      <div v-for="i in 20" :key="i" class="particle" :style="getParticleStyle(i)"></div>
    </div>

    <div class="login-container">
      <!-- Logo 区域 - 带融合背景 -->
      <div class="logo-wrapper">
        <div class="logo-glow"></div>
        <div class="logo-container">
          <img src="/logo.png" alt="Echobot Admin" class="logo" />
        </div>
      </div>

      <h1 class="login-title">管理后台</h1>
      <p class="login-subtitle">Echobot 内容管理系统</p>

      <form class="login-form" @submit.prevent="handleLogin">
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
              placeholder="管理员邮箱"
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

      <!-- 版权信息 -->
      <p class="copyright">Echobot Admin Panel v1.0</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function getParticleStyle(index: number) {
  const size = Math.random() * 4 + 2
  const left = Math.random() * 100
  const animationDuration = Math.random() * 15 + 8
  const animationDelay = Math.random() * 8

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
    await adminStore.login(email.value, password.value)
    const redirect = route.query.redirect as string || '/dashboard'
    router.push(redirect)
  } catch (err: any) {
    error.value = err.response?.data?.message || err.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
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
    radial-gradient(ellipse at 30% 20%, rgba(45, 107, 107, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(45, 107, 107, 0.1) 0%, transparent 40%),
    linear-gradient(180deg, #0d0d0d 0%, #0a0a0a 100%);
  z-index: 0;
}

/* 网格图案 - 管理后台专属 */
.grid-pattern {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(45, 107, 107, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(45, 107, 107, 0.04) 1px, transparent 1px);
  background-size: 60px 60px;
  z-index: 1;
}

/* 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 2;
}

.particle {
  position: absolute;
  bottom: -10px;
  background: rgba(45, 107, 107, 0.7);
  border-radius: 50%;
  animation: float-up linear infinite;
  box-shadow: 0 0 6px rgba(45, 107, 107, 0.5);
}

@keyframes float-up {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 0.8;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100vh) scale(0.3);
    opacity: 0;
  }
}

.login-container {
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
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(45, 107, 107, 0.6) 0%, rgba(45, 107, 107, 0.3) 40%, transparent 70%);
  border-radius: 50%;
  filter: blur(25px);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
}

.logo-container {
  width: 100px;
  height: 100px;
  border-radius: 24px;
  background: #23586a;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 60px rgba(35, 88, 106, 0.5),
    0 0 100px rgba(35, 88, 106, 0.3);
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
    rgba(45, 107, 107, 0.1) 60deg,
    transparent 120deg
  );
  animation: rotate-light 8s linear infinite;
}

@keyframes rotate-light {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.login-title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
  margin: 0;
}

.login-subtitle {
  font-size: 14px;
  color: rgba(232, 228, 212, 0.5);
  margin: 0 0 12px 0;
  letter-spacing: 1px;
}

.login-form {
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
  padding: 16px 16px 16px 48px;
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
  padding: 10px 14px;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.2);
  border-radius: 8px;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #2D6B6B 0%, #3d8080 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
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

.copyright {
  color: rgba(232, 228, 212, 0.3);
  font-size: 12px;
  margin: 20px 0 0 0;
  letter-spacing: 0.5px;
}
</style>
