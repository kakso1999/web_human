<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-logo">
        <img src="/logo.png" alt="Echobot Admin" />
      </div>

      <h1 class="login-title">管理后台</h1>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <input
            v-model="email"
            type="email"
            class="input"
            placeholder="管理员邮箱"
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
  padding: var(--spacing-lg);
}

.login-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.login-logo img {
  width: 80px;
  height: auto;
}

.login-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.login-form {
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
</style>
