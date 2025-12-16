<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Logo -->
      <div class="auth-logo">
        <img src="/logo.png" alt="Echobot" />
      </div>

      <h1 class="auth-title">登录</h1>

      <!-- 登录表单 -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <input
            v-model="email"
            type="email"
            class="input"
            placeholder="邮箱地址"
            required
          />
        </div>

        <div class="form-group">
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="密码"
            required
          />
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>

        <button type="submit" class="btn btn-accent submit-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
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
  // 跳转到 Google 登录页面
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
  padding: var(--spacing-lg);
}

.auth-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.auth-logo img {
  width: 80px;
  height: auto;
}

.auth-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.auth-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  width: 100%;
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: var(--spacing-md);
  font-size: var(--font-size-base);
  font-weight: 500;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.divider {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  color: var(--color-text-muted);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

.google-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-bg-dark-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.google-btn:hover {
  background: var(--color-bg-dark-hover);
  border-color: var(--color-border-light);
}

.google-icon {
  width: 20px;
  height: 20px;
}

.auth-link {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.auth-link a {
  color: var(--color-accent-light);
  font-weight: 500;
}

.auth-link a:hover {
  text-decoration: underline;
}
</style>
