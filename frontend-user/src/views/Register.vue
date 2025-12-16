<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">
        <img src="/logo.png" alt="Echobot" />
      </div>

      <h1 class="auth-title">注册</h1>

      <form class="auth-form" @submit.prevent="handleRegister">
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
            v-model="nickname"
            type="text"
            class="input"
            placeholder="昵称"
            required
          />
        </div>

        <div class="form-group">
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="密码 (至少8位，包含大小写字母和数字)"
            required
          />
        </div>

        <div class="form-group">
          <input
            v-model="confirmPassword"
            type="password"
            class="input"
            placeholder="确认密码"
            required
          />
        </div>

        <p v-if="error" class="error-message">{{ error }}</p>

        <button type="submit" class="btn btn-accent submit-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <p class="auth-link">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const email = ref('')
const nickname = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true

  try {
    await userStore.register(email.value, password.value, nickname.value)
    router.push('/dashboard')
  } catch (err: any) {
    error.value = err.response?.data?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
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
}

.auth-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: var(--spacing-md);
  font-weight: 500;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-link {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.auth-link a {
  color: var(--color-accent-light);
  font-weight: 500;
}
</style>
