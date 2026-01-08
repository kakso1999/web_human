<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { storyApi } from '@/api'
import type { Story } from '@/types'

const route = useRoute()
const story = ref<Story | null>(null)
const loading = ref(true)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

const videoRef = ref<HTMLVideoElement | null>(null)

onMounted(async () => {
  try {
    const res = await storyApi.getStory(route.params.id as string)
    story.value = res.data
    storyApi.recordView(route.params.id as string)
  } catch (e) {
    console.error('Failed to load story:', e)
  } finally {
    loading.value = false
  }
})

const togglePlay = () => {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const handleTimeUpdate = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
    duration.value = videoRef.value.duration
  }
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const seekTo = (e: MouseEvent) => {
  if (!videoRef.value) return
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * duration.value
}

const currentSubtitle = ref('')
const updateSubtitle = () => {
  if (!story.value?.subtitles) return
  const time = currentTime.value
  const subtitle = story.value.subtitles.find(
    s => time >= s.start && time <= s.end
  )
  currentSubtitle.value = subtitle?.text || ''
}

onMounted(() => {
  const interval = setInterval(updateSubtitle, 100)
  onUnmounted(() => clearInterval(interval))
})
</script>

<template>
  <div class="min-h-screen bg-gray-900">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="animate-spin w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>

    <!-- Video Player -->
    <div v-else-if="story" class="relative">
      <div class="relative aspect-video max-h-[80vh] mx-auto bg-black">
        <video
          ref="videoRef"
          :src="story.video_url"
          :poster="story.thumbnail_url"
          class="w-full h-full object-contain"
          @timeupdate="handleTimeUpdate"
          @ended="isPlaying = false"
        ></video>

        <!-- Subtitle Overlay -->
        <div
          v-if="currentSubtitle"
          class="absolute bottom-20 left-0 right-0 text-center px-4"
        >
          <span class="inline-block px-6 py-3 bg-black/70 text-white text-lg rounded-lg">
            {{ currentSubtitle }}
          </span>
        </div>

        <!-- Controls Overlay -->
        <div
          class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
          @click="togglePlay"
        >
          <div class="w-20 h-20 rounded-full bg-white/90 flex items-center justify-center shadow-xl">
            <svg v-if="!isPlaying" class="w-10 h-10 text-primary-500 ml-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
            <svg v-else class="w-10 h-10 text-primary-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="absolute bottom-0 left-0 right-0 px-4 pb-4">
          <div
            class="h-2 bg-white/30 rounded-full cursor-pointer overflow-hidden"
            @click="seekTo"
          >
            <div
              class="h-full bg-primary-500 rounded-full transition-all"
              :style="{ width: `${(currentTime / duration) * 100}%` }"
            ></div>
          </div>
          <div class="flex justify-between text-white/80 text-sm mt-2">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>

      <!-- Story Info -->
      <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="bg-white rounded-2xl p-6 shadow-soft">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ story.title_en || story.title }}</h1>
              <div class="flex items-center gap-4 mt-3 text-gray-600">
                <span class="px-3 py-1 bg-primary-50 text-primary-600 text-sm font-medium rounded-full">
                  {{ story.category_name }}
                </span>
                <span>{{ story.view_count }} views</span>
                <span>{{ formatTime(story.duration) }}</span>
              </div>
            </div>
            <RouterLink
              :to="`/studio?story_id=${story.id}`"
              class="btn-primary"
            >
              Tell with My Voice
            </RouterLink>
          </div>

          <p v-if="story.description" class="mt-6 text-gray-600 leading-relaxed">
            {{ story.description }}
          </p>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="flex flex-col items-center justify-center min-h-screen text-white">
      <h2 class="text-2xl font-bold mb-4">Story Not Found</h2>
      <RouterLink to="/discover" class="btn-primary">
        Browse Stories
      </RouterLink>
    </div>
  </div>
</template>
