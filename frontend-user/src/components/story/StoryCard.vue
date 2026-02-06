<script setup lang="ts">
import { computed } from 'vue'
import type { Story } from '@/types'
import ShareMenu from '@/components/common/ShareMenu.vue'

interface Props {
  story: Story
}

const props = defineProps<Props>()

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 生成分享链接
const shareUrl = computed(() => {
  return `${window.location.origin}/story/${props.story.id}`
})
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
      <!-- Share Button -->
      <div class="share-btn-wrapper absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
        <ShareMenu
          :url="shareUrl"
          :title="story.title_en || story.title"
          :description="story.description_en || story.description || ''"
          :imageUrl="story.thumbnail_url"
        />
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

<style scoped>
.share-btn-wrapper :deep(.share-btn) {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.share-btn-wrapper :deep(.share-btn):hover {
  background: white;
}
</style>
