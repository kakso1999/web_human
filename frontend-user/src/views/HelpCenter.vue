<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">Help Center</h1>

      <!-- Search -->
      <div class="bg-white rounded-2xl shadow-soft p-6 mb-8">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search for help..."
          class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      <!-- Categories -->
      <div class="grid md:grid-cols-2 gap-6 mb-8">
        <div
          v-for="category in categories"
          :key="category.title"
          class="bg-white rounded-2xl shadow-soft p-6 hover:shadow-md transition-shadow cursor-pointer"
          @click="selectedCategory = category"
        >
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="category.icon === 'mic'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              <path v-else-if="category.icon === 'film'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
              <path v-else-if="category.icon === 'book'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ category.title }}</h3>
          <p class="text-gray-600 text-sm">{{ category.description }}</p>
        </div>
      </div>

      <!-- Popular Articles -->
      <div class="bg-white rounded-2xl shadow-soft p-6">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Popular Articles</h2>
        <div class="space-y-4">
          <div
            v-for="article in articles"
            :key="article.title"
            class="p-4 border border-gray-100 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <h4 class="font-medium text-gray-900 mb-1">{{ article.title }}</h4>
            <p class="text-sm text-gray-500">{{ article.preview }}</p>
          </div>
        </div>
      </div>

      <!-- Contact Support -->
      <div class="mt-8 text-center">
        <p class="text-gray-600 mb-4">Can't find what you're looking for?</p>
        <RouterLink to="/contact" class="btn-primary inline-block">
          Contact Support
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const searchQuery = ref('')
const selectedCategory = ref(null)

const categories = [
  {
    icon: 'mic',
    title: 'Voice Cloning',
    description: 'Learn how to create and manage voice profiles'
  },
  {
    icon: 'film',
    title: 'Story Generation',
    description: 'Guide to generating personalized stories'
  },
  {
    icon: 'book',
    title: 'Audiobooks',
    description: 'Creating audiobooks with custom voices'
  },
  {
    icon: 'card',
    title: 'Billing & Plans',
    description: 'Subscription plans and payment information'
  }
]

const articles = [
  {
    title: 'How to create your first voice profile',
    preview: 'Step-by-step guide to recording and creating a voice profile for story generation.'
  },
  {
    title: 'Understanding story generation limits',
    preview: 'Learn about the different plan limits and how to maximize your usage.'
  },
  {
    title: 'Troubleshooting audio quality issues',
    preview: 'Tips for improving voice recording quality and common fixes.'
  },
  {
    title: 'How to upgrade or downgrade your plan',
    preview: 'Guide to changing your subscription plan and what happens to your data.'
  },
  {
    title: 'Exporting and sharing your creations',
    preview: 'Learn how to download and share your generated stories and audiobooks.'
  }
]
</script>
