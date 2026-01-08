<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const nickname = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreeTerms = ref(false)
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  if (!nickname.value || !email.value || !password.value) {
    error.value = 'Please fill in all required fields'
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }

  if (!agreeTerms.value) {
    error.value = 'Please agree to the Terms of Service and Privacy Policy'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await userStore.register(email.value, password.value, nickname.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}

const handleGoogleLogin = async () => {
  try {
    const res = await authApi.getGoogleAuthUrl()
    window.location.href = res.data.url
  } catch (e) {
    error.value = 'Google login is not available'
  }
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left Side - Image -->
    <div class="hidden lg:block lg:w-1/2 bg-gradient-hero relative overflow-hidden">
      <div class="absolute inset-0 flex items-center justify-center p-12">
        <div class="text-center text-white">
          <h2 class="text-4xl font-bold mb-4">
            Join Echobot<br/>Start Your Story Journey
          </h2>
          <p class="text-lg text-white/80 max-w-md mx-auto">
            Use AI technology to share love and warmth. Create unique story experiences for your family.
          </p>

          <div class="mt-10 space-y-4 text-left max-w-sm mx-auto">
            <div class="flex items-center gap-3 bg-white/10 rounded-xl px-4 py-3">
              <img src="/icons/icon-microphone.png" alt="" class="w-6 h-6 object-contain" />
              <span class="text-white/90">Voice Cloning Technology</span>
            </div>
            <div class="flex items-center gap-3 bg-white/10 rounded-xl px-4 py-3">
              <img src="/icons/icon-family.png" alt="" class="w-6 h-6 object-contain" />
              <span class="text-white/90">Digital Human Avatar</span>
            </div>
            <div class="flex items-center gap-3 bg-white/10 rounded-xl px-4 py-3">
              <img src="/icons/icon-books.png" alt="" class="w-6 h-6 object-contain" />
              <span class="text-white/90">Curated Story Library</span>
            </div>
          </div>
        </div>
      </div>

      <svg class="absolute bottom-0 left-0 right-0" viewBox="0 0 1440 200" fill="none">
        <path
          d="M0 200L60 180C120 160 240 120 360 100C480 80 600 80 720 90C840 100 960 120 1080 125C1200 130 1320 120 1380 115L1440 110V200H0Z"
          fill="white"
          fill-opacity="0.1"
        />
      </svg>
    </div>

    <!-- Right Side - Form -->
    <div class="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
      <div class="w-full max-w-md">
        <RouterLink to="/" class="flex items-center gap-2 justify-center mb-8">
          <img src="/logo2.jpg" alt="Echobot" class="h-12 rounded-lg" />
        </RouterLink>

        <div class="text-center mb-8">
          <h1 class="text-3xl font-bold text-gray-900">Create Account</h1>
          <p class="mt-2 text-gray-600">Sign up free and start your story journey</p>
        </div>

        <button
          @click="handleGoogleLogin"
          class="w-full flex items-center justify-center gap-3 px-6 py-3 border-2 border-gray-200 rounded-xl font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>

        <div class="flex items-center gap-4 my-6">
          <div class="flex-1 h-px bg-gray-200"></div>
          <span class="text-sm text-gray-500">or</span>
          <div class="flex-1 h-px bg-gray-200"></div>
        </div>

        <div
          v-if="error"
          class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm"
        >
          {{ error }}
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input
              v-model="nickname"
              type="text"
              placeholder="Your name"
              class="input"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="Enter your email"
              class="input"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              v-model="password"
              type="password"
              placeholder="At least 6 characters"
              class="input"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="Enter password again"
              class="input"
              required
            />
          </div>

          <label class="flex items-start gap-3 cursor-pointer pt-2">
            <input
              v-model="agreeTerms"
              type="checkbox"
              class="w-4 h-4 mt-0.5 text-primary-500 border-gray-300 rounded focus:ring-primary-500"
            />
            <span class="text-sm text-gray-600">
              I agree to the
              <a href="/terms" class="text-primary-500 hover:underline">Terms of Service</a>
              and
              <a href="/privacy" class="text-primary-500 hover:underline">Privacy Policy</a>
            </span>
          </label>

          <button
            type="submit"
            :disabled="loading"
            class="btn-primary w-full py-3.5 mt-2"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            {{ loading ? 'Creating account...' : 'Create Account' }}
          </button>
        </form>

        <p class="mt-8 text-center text-gray-600">
          Already have an account?
          <RouterLink to="/login" class="text-primary-500 font-medium hover:text-primary-600">
            Sign in
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
