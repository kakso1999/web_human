<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { digitalHumanApi } from '@/api'
import type { AvatarProfile } from '@/types'

const profiles = ref<AvatarProfile[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await digitalHumanApi.getProfiles()
    profiles.value = res.data.profiles
  } finally {
    loading.value = false
  }
})

const deleteProfile = async (id: string) => {
  if (!confirm('Are you sure you want to delete this avatar profile?')) return
  try {
    await digitalHumanApi.deleteProfile(id)
    profiles.value = profiles.value.filter(p => p.id !== id)
  } catch (e) {
    alert('Failed to delete')
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-gray-900">Avatar Profiles</h2>
      <RouterLink to="/studio" class="btn-primary text-sm">
        Add New Avatar
      </RouterLink>
    </div>

    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="animate-pulse">
        <div class="bg-gray-200 rounded-xl aspect-square"></div>
        <div class="mt-2 h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
    </div>

    <div v-else-if="profiles.length === 0" class="text-center py-12">
      <div class="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <img src="/icons/icon-avatar.png" alt="" class="w-10 h-10 object-contain" />
      </div>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">No Avatar Profiles Yet</h3>
      <p class="text-gray-500 mb-4">Upload a photo to create your digital avatar</p>
      <RouterLink to="/studio" class="btn-primary">
        Create Avatar Profile
      </RouterLink>
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-6">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="group relative"
      >
        <div class="relative rounded-xl overflow-hidden aspect-square">
          <img
            :src="profile.image_url"
            :alt="profile.name"
            class="w-full h-full object-cover"
          />
          <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button
              v-if="profile.preview_video_url"
              class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-primary-500 hover:bg-gray-100"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
            <button
              @click="deleteProfile(profile.id)"
              class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-red-500 hover:bg-gray-100"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="mt-3">
          <h3 class="font-medium text-gray-900">{{ profile.name }}</h3>
          <p class="text-sm text-gray-500">{{ new Date(profile.created_at).toLocaleDateString() }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
