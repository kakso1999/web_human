<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storyGenerationApi } from '@/api'
import type { StoryGenerationJob } from '@/types'

const jobs = ref<StoryGenerationJob[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await storyGenerationApi.getJobs({ page_size: 20 })
    jobs.value = res.data.items
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-gray-900">My Creations</h2>
      <RouterLink to="/studio" class="btn-primary text-sm">
        Create New
      </RouterLink>
    </div>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="animate-pulse flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
        <div class="w-24 h-16 bg-gray-200 rounded-lg"></div>
        <div class="flex-1">
          <div class="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div class="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    </div>

    <div v-else-if="jobs.length === 0" class="text-center py-12">
      <div class="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <img src="/icons/icon-video.png" alt="" class="w-10 h-10 object-contain" />
      </div>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">No Creations Yet</h3>
      <p class="text-gray-500 mb-4">Use the AI Studio to create your first story video</p>
      <RouterLink to="/studio" class="btn-primary">
        Start Creating
      </RouterLink>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="job in jobs"
        :key="job.id"
        class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
      >
        <div class="w-24 h-16 rounded-lg overflow-hidden bg-gray-200 flex-shrink-0">
          <video
            v-if="job.output_video_url"
            :src="job.output_video_url"
            class="w-full h-full object-cover"
          ></video>
          <div v-else class="w-full h-full flex items-center justify-center">
            <img src="/icons/icon-video.png" alt="" class="w-8 h-8 object-contain" />
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-900">Story #{{ job.id.slice(-6) }}</h3>
          <p class="text-sm text-gray-500">{{ new Date(job.created_at).toLocaleDateString() }}</p>
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
                 job.status === 'processing' ? `Processing ${job.progress}%` :
                 job.status === 'failed' ? 'Failed' : 'Pending' }}
            </span>
          </div>
        </div>
        <div v-if="job.status === 'completed' && job.output_video_url" class="flex gap-2">
          <RouterLink
            :to="`/story/${job.story_id}`"
            class="p-2 text-gray-500 hover:text-primary-500"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </RouterLink>
          <a
            :href="job.output_video_url"
            download
            class="p-2 text-gray-500 hover:text-primary-500"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
