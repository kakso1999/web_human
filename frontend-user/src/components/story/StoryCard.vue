<script setup lang="ts">
import type { Story } from '@/types'

interface Props {
  story: Story
}

defineProps<Props>()

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <RouterLink
    :to="`/story/${story.id}`"
    class="story-card group block"
  >
    <!-- Image -->
    <div class="relative overflow-hidden">
      <img
        :src="story.thumbnail_url"
        :alt="story.title"
        class="story-card-image transition-transform duration-500 group-hover:scale-110"
      />
      <!-- Overlay -->
      <div class="story-card-overlay"></div>
      <!-- Play Button -->
      <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div class="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
          <svg class="w-6 h-6 text-primary-500 ml-1" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>
      <!-- Duration Badge -->
      <div class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs rounded-md">
        {{ formatDuration(story.duration) }}
      </div>
    </div>

    <!-- Content -->
    <div class="p-4">
      <h3 class="font-semibold text-gray-900 line-clamp-2 group-hover:text-primary-500 transition-colors">
        {{ story.title_en || story.title }}
      </h3>
      <div class="mt-2 flex items-center gap-2">
        <span class="px-2 py-0.5 bg-primary-50 text-primary-600 text-xs font-medium rounded-full">
          {{ story.category_name }}
        </span>
        <span class="text-xs text-gray-500">
          {{ story.view_count }} views
        </span>
      </div>
    </div>
  </RouterLink>
</template>
