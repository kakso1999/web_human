<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { name: 'Voice Profiles', path: '/profiles/voice' },
  { name: 'Avatar Profiles', path: '/profiles/avatar' },
  { name: 'My Creations', path: '/profiles/creations' },
  { name: 'Account', path: '/account', external: true }
]

const currentTab = computed(() => route.path)
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">My Profiles</h1>
        <p class="mt-2 text-gray-600">Manage your voice and avatar profiles</p>
      </div>

      <!-- Tabs -->
      <div class="flex gap-2 mb-8 flex-wrap">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          :class="[
            'px-6 py-3 rounded-xl font-medium transition-all',
            currentTab === tab.path || (tab.external && currentTab.startsWith(tab.path))
              ? 'bg-primary-500 text-white shadow-lg'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          ]"
        >
          {{ tab.name }}
        </RouterLink>
      </div>

      <!-- Content -->
      <div class="bg-white rounded-2xl shadow-soft p-6">
        <RouterView />
      </div>
    </div>
  </div>
</template>
