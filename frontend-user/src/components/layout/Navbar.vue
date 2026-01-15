<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isMenuOpen = ref(false)
const isScrolled = ref(false)

if (typeof window !== 'undefined') {
  window.addEventListener('scroll', () => {
    isScrolled.value = window.scrollY > 20
  })
}

const navLinks = [
  { name: 'Discover', path: '/discover' },
  { name: 'Create Profile', path: '/create-profile' },
  { name: 'AI Studio', path: '/studio' },
  { name: 'Audiobook', path: '/audiobook' },
  { name: 'Pricing', path: '/subscription' },
]

const isActive = (path: string) => route.path === path

const handleLogout = () => {
  userStore.logout()
  router.push('/')
}
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
    :class="[
      isScrolled ? 'bg-white/95 backdrop-blur-md shadow-soft' : 'bg-transparent'
    ]"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 lg:h-20">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-2">
          <img
            src="/logo2.jpg"
            alt="Echobot"
            class="h-10 lg:h-12 rounded-lg"
          />
        </RouterLink>

        <!-- Desktop Navigation -->
        <nav class="hidden lg:flex items-center gap-8">
          <RouterLink
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="text-base font-medium transition-colors hover:text-primary-500"
            :class="[
              isActive(link.path) ? 'text-primary-500' : 'text-gray-700'
            ]"
          >
            {{ link.name }}
          </RouterLink>
        </nav>

        <!-- Desktop Auth Buttons -->
        <div class="hidden lg:flex items-center gap-4">
          <template v-if="userStore.isLoggedIn">
            <RouterLink
              to="/profiles"
              class="flex items-center gap-2 text-gray-700 hover:text-primary-500 transition-colors"
            >
              <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden">
                <img
                  v-if="userStore.user?.avatar_url"
                  :src="userStore.user.avatar_url"
                  alt="Avatar"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-primary-500 font-medium">
                  {{ userStore.user?.nickname?.[0] || 'U' }}
                </span>
              </div>
              <span class="font-medium">{{ userStore.user?.nickname }}</span>
            </RouterLink>
            <button
              @click="handleLogout"
              class="text-gray-500 hover:text-gray-700 transition-colors"
            >
              Logout
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="text-gray-700 font-medium hover:text-primary-500 transition-colors"
            >
              Log In
            </RouterLink>
            <RouterLink
              to="/register"
              class="btn-primary text-sm py-2 px-5"
            >
              Get Started
            </RouterLink>
          </template>
        </div>

        <!-- Mobile Menu Button -->
        <button
          @click="isMenuOpen = !isMenuOpen"
          class="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              v-if="!isMenuOpen"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
            <path
              v-else
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile Menu -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="isMenuOpen"
        class="lg:hidden bg-white border-t shadow-lg"
      >
        <div class="px-4 py-4 space-y-2">
          <RouterLink
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            @click="isMenuOpen = false"
            class="block px-4 py-3 rounded-xl font-medium transition-colors"
            :class="[
              isActive(link.path)
                ? 'bg-primary-50 text-primary-500'
                : 'text-gray-700 hover:bg-gray-50'
            ]"
          >
            {{ link.name }}
          </RouterLink>

          <div class="pt-4 border-t mt-4">
            <template v-if="userStore.isLoggedIn">
              <RouterLink
                to="/profiles"
                @click="isMenuOpen = false"
                class="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-50"
              >
                <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span class="text-primary-500 font-medium">
                    {{ userStore.user?.nickname?.[0] || 'U' }}
                  </span>
                </div>
                <div>
                  <div class="font-medium">{{ userStore.user?.nickname }}</div>
                  <div class="text-sm text-gray-500">View Profile</div>
                </div>
              </RouterLink>
              <button
                @click="handleLogout(); isMenuOpen = false"
                class="w-full mt-2 px-4 py-3 text-left text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </template>
            <template v-else>
              <RouterLink
                to="/login"
                @click="isMenuOpen = false"
                class="block w-full px-4 py-3 text-center text-gray-700 font-medium rounded-xl border-2 border-gray-200"
              >
                Log In
              </RouterLink>
              <RouterLink
                to="/register"
                @click="isMenuOpen = false"
                class="block w-full mt-2 px-4 py-3 text-center text-white font-medium rounded-xl bg-primary-500"
              >
                Get Started
              </RouterLink>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </header>

  <!-- Spacer -->
  <div class="h-16 lg:h-20"></div>
</template>
