<template>
  <div class="auth-callback">
    <div class="loading-container">
      <div class="spinner"></div>
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const message = ref('Signing you in...')

onMounted(async () => {
  const accessToken = route.query.access_token as string
  const userId = route.query.user_id as string
  const nickname = route.query.nickname as string
  const error = route.query.error as string

  if (error) {
    message.value = 'Login failed. Redirecting...'
    setTimeout(() => {
      router.push('/login?error=' + error)
    }, 1500)
    return
  }

  if (accessToken && userId) {
    // Save token to localStorage
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user_id', userId)

    // Update user store
    userStore.setUser({
      id: userId,
      nickname: nickname || 'User',
      email: '',
      avatar_url: ''
    })
    userStore.setToken(accessToken)

    message.value = 'Success! Redirecting...'

    // Redirect to home or original destination
    setTimeout(() => {
      const redirect = localStorage.getItem('auth_redirect') || '/'
      localStorage.removeItem('auth_redirect')
      router.push(redirect)
    }, 500)
  } else {
    message.value = 'Invalid callback. Redirecting...'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  }
})
</script>

<style scoped>
.auth-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 100%);
}

.loading-container {
  text-align: center;
  color: #fff;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #2D6B6B;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

p {
  font-size: 16px;
  color: #b3b3b3;
}
</style>
