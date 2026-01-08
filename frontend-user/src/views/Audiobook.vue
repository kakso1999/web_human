<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { audiobookApi, voiceCloneApi } from '@/api'
import type { AudiobookStory, VoiceProfile, AudiobookJob } from '@/types'

const stories = ref<AudiobookStory[]>([])
const voiceProfiles = ref<VoiceProfile[]>([])
const jobs = ref<AudiobookJob[]>([])
const loading = ref(true)
const selectedStory = ref<AudiobookStory | null>(null)
const selectedVoice = ref<VoiceProfile | null>(null)
const showModal = ref(false)
const generating = ref(false)

onMounted(async () => {
  try {
    const [storiesRes, profilesRes, jobsRes] = await Promise.all([
      audiobookApi.getStories({ page_size: 20 }),
      voiceCloneApi.getProfiles(),
      audiobookApi.getJobs({ page_size: 10 })
    ])
    stories.value = storiesRes.data.items
    voiceProfiles.value = profilesRes.data.profiles
    jobs.value = jobsRes.data.items
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
})

const openCreateModal = (story: AudiobookStory) => {
  selectedStory.value = story
  showModal.value = true
}

const createAudiobook = async () => {
  if (!selectedStory.value || !selectedVoice.value) return

  generating.value = true
  try {
    const res = await audiobookApi.createJob(selectedStory.value.id, selectedVoice.value.id)
    jobs.value.unshift(res.data)
    showModal.value = false
    selectedStory.value = null
    selectedVoice.value = null
  } catch (e) {
    alert('Creation failed, please try again')
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Audiobook</h1>
        <p class="mt-2 text-gray-600">Generate audiobooks with your voice</p>
      </div>

      <!-- My Audiobooks -->
      <div v-if="jobs.length > 0" class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">My Audiobooks</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="job in jobs"
            :key="job.id"
            class="bg-white rounded-xl p-4 shadow-soft"
          >
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 rounded-lg bg-primary-50 flex items-center justify-center">
                <img src="/icons/icon-storybook.png" alt="" class="w-8 h-8 object-contain" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-900 truncate">{{ job.story_title }}</h3>
                <p class="text-sm text-gray-500">{{ job.voice_name }}</p>
                <div class="mt-1">
                  <span
                    :class="[
                      'text-xs px-2 py-0.5 rounded-full',
                      job.status === 'completed' ? 'bg-green-100 text-green-700' :
                      job.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                      job.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    ]"
                  >
                    {{ job.status === 'completed' ? 'Completed' :
                       job.status === 'processing' ? 'Processing' :
                       job.status === 'failed' ? 'Failed' : 'Pending' }}
                  </span>
                </div>
              </div>
              <audio
                v-if="job.status === 'completed' && job.audio_url"
                :src="job.audio_url"
                controls
                class="w-32"
              ></audio>
            </div>
          </div>
        </div>
      </div>

      <!-- Available Stories -->
      <div>
        <h2 class="text-xl font-bold text-gray-900 mb-4">Story Templates</h2>

        <div v-if="loading" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="i in 6" :key="i" class="animate-pulse bg-white rounded-xl p-4">
            <div class="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div class="h-20 bg-gray-200 rounded mb-3"></div>
            <div class="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="story in stories"
            :key="story.id"
            class="bg-white rounded-xl p-6 shadow-soft hover:shadow-card transition-shadow"
          >
            <h3 class="font-bold text-gray-900 mb-2">{{ story.title }}</h3>
            <p class="text-gray-600 text-sm line-clamp-3 mb-4">
              {{ story.content.substring(0, 150) }}...
            </p>
            <div class="flex items-center justify-between">
              <div class="flex gap-2">
                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {{ story.language === 'zh' ? 'Chinese' : 'English' }}
                </span>
                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {{ story.category }}
                </span>
              </div>
              <button
                @click="openCreateModal(story)"
                class="btn-primary text-sm py-2 px-4"
              >
                Create Audiobook
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div class="absolute inset-0 bg-black/50" @click="showModal = false"></div>
        <div class="relative bg-white rounded-2xl p-6 max-w-md w-full shadow-xl">
          <h3 class="text-xl font-bold text-gray-900 mb-4">Select Voice</h3>

          <div v-if="voiceProfiles.length === 0" class="text-center py-8 text-gray-500">
            <p>You don't have any voice profiles yet</p>
            <RouterLink to="/studio" class="text-primary-500 hover:underline">
              Create a voice profile
            </RouterLink>
          </div>

          <div v-else class="space-y-3 max-h-64 overflow-y-auto">
            <div
              v-for="profile in voiceProfiles"
              :key="profile.id"
              @click="selectedVoice = profile"
              :class="[
                'p-4 rounded-xl border-2 cursor-pointer transition-all',
                selectedVoice?.id === profile.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <p class="font-medium text-gray-900">{{ profile.name }}</p>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="showModal = false"
              class="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="createAudiobook"
              :disabled="!selectedVoice || generating"
              class="flex-1 btn-primary disabled:opacity-50"
            >
              {{ generating ? 'Creating...' : 'Start Generation' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
