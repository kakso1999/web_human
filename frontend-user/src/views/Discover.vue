<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storyApi } from '@/api'
import type { Story, Category } from '@/types'
import StoryCard from '@/components/story/StoryCard.vue'

const route = useRoute()
const router = useRouter()

const stories = ref<Story[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const totalPages = ref(1)

const currentPage = computed(() => Number(route.query.page) || 1)
const currentCategory = computed(() => route.query.category as string || '')
const searchQuery = computed(() => route.query.q as string || '')

const fetchData = async () => {
  loading.value = true
  try {
    const [storiesRes, categoriesRes] = await Promise.all([
      storyApi.getStories({
        page: currentPage.value,
        page_size: 12,
        category_id: currentCategory.value || undefined,
        search: searchQuery.value || undefined
      }),
      categories.value.length === 0 ? storyApi.getCategories() : Promise.resolve({ data: categories.value })
    ])
    stories.value = storiesRes.data.items
    totalPages.value = Math.ceil(storiesRes.data.total / storiesRes.data.page_size)

    if (Array.isArray(categoriesRes.data)) {
      categories.value = categoriesRes.data
    }
  } catch (e) {
    console.error('Failed to fetch stories:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
watch([currentPage, currentCategory, searchQuery], fetchData)

const selectCategory = (categoryId: string) => {
  router.push({
    query: {
      ...route.query,
      category: categoryId || undefined,
      page: undefined
    }
  })
}

const handleSearch = (e: Event) => {
  const target = e.target as HTMLInputElement
  router.push({
    query: {
      ...route.query,
      q: target.value || undefined,
      page: undefined
    }
  })
}

const goToPage = (page: number) => {
  router.push({
    query: {
      ...route.query,
      page: page > 1 ? page : undefined
    }
  })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Discover Stories</h1>
        <p class="mt-2 text-gray-600">Find amazing stories and tell them with your voice</p>
      </div>

      <!-- Search & Filter -->
      <div class="flex flex-col lg:flex-row gap-4 mb-8">
        <!-- Search -->
        <div class="relative flex-1 max-w-md">
          <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
            type="text"
            :value="searchQuery"
            @input="handleSearch"
            placeholder="Search stories..."
            class="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-primary-500 focus:ring-4 focus:ring-primary-100 outline-none transition-all"
          />
        </div>

        <!-- Categories -->
        <div class="flex gap-2 overflow-x-auto pb-2 lg:pb-0 scrollbar-hide">
          <button
            @click="selectCategory('')"
            :class="[
              'px-4 py-2 rounded-full font-medium whitespace-nowrap transition-colors',
              !currentCategory
                ? 'bg-primary-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            ]"
          >
            All
          </button>
          <button
            v-for="category in categories"
            :key="category.id"
            @click="selectCategory(category.id)"
            :class="[
              'px-4 py-2 rounded-full font-medium whitespace-nowrap transition-colors',
              currentCategory === category.id
                ? 'bg-primary-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            ]"
          >
            {{ category.name_en || category.name }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div v-for="i in 8" :key="i" class="animate-pulse">
          <div class="bg-gray-200 rounded-2xl aspect-[4/3]"></div>
          <div class="mt-4 h-4 bg-gray-200 rounded w-3/4"></div>
          <div class="mt-2 h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="stories.length === 0"
        class="text-center py-20"
      >
        <div class="w-24 h-24 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No Stories Found</h3>
        <p class="text-gray-600">Try a different search term?</p>
      </div>

      <!-- Story Grid -->
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <StoryCard
          v-for="story in stories"
          :key="story.id"
          :story="story"
        />
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-12 flex justify-center gap-2">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Previous
        </button>

        <template v-for="page in totalPages" :key="page">
          <button
            v-if="page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)"
            @click="goToPage(page)"
            :class="[
              'w-10 h-10 rounded-lg font-medium transition-colors',
              page === currentPage
                ? 'bg-primary-500 text-white'
                : 'border border-gray-200 text-gray-700 hover:bg-gray-100'
            ]"
          >
            {{ page }}
          </button>
          <span
            v-else-if="page === currentPage - 2 || page === currentPage + 2"
            class="px-2 text-gray-400"
          >
            ...
          </span>
        </template>

        <button
          @click="goToPage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
