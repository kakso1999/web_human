<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { storyGenerationApi, audiobookApi } from '@/api'
import type { StoryGenerationJob, AudiobookJob } from '@/types'

// Story generation jobs
const storyJobs = ref<StoryGenerationJob[]>([])
const audiobookJobs = ref<AudiobookJob[]>([])
const loading = ref(true)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const hasMore = computed(() => storyJobs.value.length < total.value)

// 任务类型过滤
const activeTab = ref<'story' | 'audiobook'>('story')

// 状态过滤
const statusFilter = ref<string>('all')

const loadStoryJobs = async (append = false) => {
  loading.value = true
  try {
    const res = await storyGenerationApi.getJobs({
      page: page.value,
      page_size: pageSize.value
    })
    if (append) {
      storyJobs.value = [...storyJobs.value, ...res.data.items]
    } else {
      storyJobs.value = res.data.items
    }
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const loadAudiobookJobs = async () => {
  try {
    const res = await audiobookApi.getJobs({ page_size: 20 })
    audiobookJobs.value = res.data.items
  } catch (e) {
    console.error('Failed to load audiobook jobs', e)
  }
}

onMounted(async () => {
  await Promise.all([loadStoryJobs(), loadAudiobookJobs()])
})

const loadMore = async () => {
  if (!hasMore.value || loading.value) return
  page.value++
  await loadStoryJobs(true)
}

const refreshJobs = async () => {
  page.value = 1
  await loadStoryJobs()
}

// 过滤后的任务列表
const filteredStoryJobs = computed(() => {
  if (statusFilter.value === 'all') return storyJobs.value
  return storyJobs.value.filter(job => job.status === statusFilter.value)
})

const filteredAudiobookJobs = computed(() => {
  if (statusFilter.value === 'all') return audiobookJobs.value
  return audiobookJobs.value.filter(job => job.status === statusFilter.value)
})

// 获取状态样式
const getStatusClass = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'processing':
      return 'bg-blue-100 text-blue-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

const getStatusText = (status: string, progress?: number) => {
  switch (status) {
    case 'completed':
      return 'Completed'
    case 'processing':
      return progress ? `Processing ${progress}%` : 'Processing...'
    case 'failed':
      return 'Failed'
    default:
      return 'Pending'
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-gray-900">My Creations</h2>
      <div class="flex items-center gap-3">
        <button @click="refreshJobs" class="btn-secondary text-sm" :disabled="loading">
          Refresh
        </button>
        <RouterLink to="/studio" class="btn-primary text-sm">
          Create New
        </RouterLink>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-2 mb-4">
      <button
        @click="activeTab = 'story'"
        :class="[
          'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
          activeTab === 'story'
            ? 'bg-primary-500 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        Story Videos
      </button>
      <button
        @click="activeTab = 'audiobook'"
        :class="[
          'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
          activeTab === 'audiobook'
            ? 'bg-primary-500 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        Audiobooks
      </button>
    </div>

    <!-- 状态过滤 -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="status in ['all', 'completed', 'processing', 'pending', 'failed']"
        :key="status"
        @click="statusFilter = status"
        :class="[
          'px-3 py-1 rounded-full text-xs font-medium transition-colors',
          statusFilter === status
            ? 'bg-primary-100 text-primary-700'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
      >
        {{ status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1) }}
      </button>
    </div>

    <!-- Story Videos -->
    <template v-if="activeTab === 'story'">
      <div v-if="loading && storyJobs.length === 0" class="space-y-4">
        <div v-for="i in 3" :key="i" class="animate-pulse flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
          <div class="w-24 h-16 bg-gray-200 rounded-lg"></div>
          <div class="flex-1">
            <div class="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div class="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
        </div>
      </div>

      <div v-else-if="filteredStoryJobs.length === 0" class="text-center py-12">
        <div class="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <img src="/icons/icon-sparkles.png" alt="" class="w-10 h-10 object-contain" />
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">No Story Videos Yet</h3>
        <p class="text-gray-500 mb-4">Use the AI Studio to create your first story video</p>
        <RouterLink to="/studio" class="btn-primary">
          Start Creating
        </RouterLink>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="job in filteredStoryJobs"
          :key="job.id"
          class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <div class="w-24 h-16 rounded-lg overflow-hidden bg-gray-200 flex-shrink-0">
            <video
              v-if="job.final_video_url"
              :src="job.final_video_url"
              class="w-full h-full object-cover"
            ></video>
            <div v-else class="w-full h-full flex items-center justify-center">
              <img src="/icons/icon-sparkles.png" alt="" class="w-8 h-8 object-contain opacity-50" />
            </div>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900">Story Generation #{{ job.id.slice(-6) }}</h3>
            <p class="text-sm text-gray-500">{{ formatDateTime(job.created_at) }}</p>
            <div class="flex items-center gap-2 mt-1">
              <span :class="['text-xs px-2 py-0.5 rounded-full', getStatusClass(job.status)]">
                {{ getStatusText(job.status, job.progress) }}
              </span>
              <span v-if="job.current_step && job.status === 'processing'" class="text-xs text-gray-500">
                {{ job.current_step }}
              </span>
            </div>
            <p v-if="job.status === 'failed' && job.error" class="text-xs text-red-500 mt-1 truncate">
              {{ job.error }}
            </p>
          </div>
          <div v-if="job.status === 'completed' && job.final_video_url" class="flex items-center gap-2">
            <RouterLink
              :to="`/story/${job.story_id}`"
              class="p-2 text-gray-500 hover:text-primary-500 rounded-lg hover:bg-gray-200"
              title="View Story"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </RouterLink>
            <a
              :href="job.final_video_url"
              download
              class="p-2 text-gray-500 hover:text-primary-500 rounded-lg hover:bg-gray-200"
              title="Download"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
            </a>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore" class="text-center pt-4">
          <button @click="loadMore" :disabled="loading" class="btn-secondary">
            {{ loading ? 'Loading...' : 'Load More' }}
          </button>
        </div>
      </div>
    </template>

    <!-- Audiobooks -->
    <template v-else-if="activeTab === 'audiobook'">
      <div v-if="filteredAudiobookJobs.length === 0" class="text-center py-12">
        <div class="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <img src="/icons/icon-microphone.png" alt="" class="w-10 h-10 object-contain" />
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-2">No Audiobooks Yet</h3>
        <p class="text-gray-500 mb-4">Create audiobooks with your cloned voice</p>
        <RouterLink to="/audiobook" class="btn-primary">
          Create Audiobook
        </RouterLink>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="job in filteredAudiobookJobs"
          :key="job.id"
          class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <div class="w-16 h-16 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
            <img src="/icons/icon-microphone.png" alt="" class="w-8 h-8 object-contain" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900">{{ job.story_title || 'Audiobook' }}</h3>
            <p class="text-sm text-gray-500">Voice: {{ job.voice_name || 'Custom' }}</p>
            <div class="flex items-center gap-2 mt-1">
              <span :class="['text-xs px-2 py-0.5 rounded-full', getStatusClass(job.status)]">
                {{ getStatusText(job.status, job.progress) }}
              </span>
            </div>
          </div>
          <div v-if="job.status === 'completed' && job.audio_url" class="flex items-center gap-2">
            <audio :src="job.audio_url" controls class="w-48"></audio>
            <a
              :href="job.audio_url"
              download
              class="p-2 text-gray-500 hover:text-primary-500 rounded-lg hover:bg-gray-200"
              title="Download"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
