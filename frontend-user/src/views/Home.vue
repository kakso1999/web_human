<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storyApi } from '@/api'
import type { Story, Category } from '@/types'
import StoryCard from '@/components/story/StoryCard.vue'

const stories = ref<Story[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [storiesRes, categoriesRes] = await Promise.all([
      storyApi.getRandomStories(8),
      storyApi.getCategories()
    ])
    stories.value = storiesRes.data
    categories.value = categoriesRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
})

const features = [
  {
    icon: '/icons/icon-microphone.png',
    title: 'Voice Cloning',
    description: 'Upload a voice sample and our AI will learn your unique voice to narrate stories.'
  },
  {
    icon: '/icons/icon-family.png',
    title: 'Digital Human',
    description: 'Upload a photo to create your digital avatar that tells stories to your kids.'
  },
  {
    icon: '/icons/icon-books.png',
    title: 'Story Library',
    description: 'Access hundreds of curated children\'s stories designed to educate and entertain.'
  }
]

const useCases = [
  {
    image: '/images/feature-travel-connection.png',
    title: 'For Traveling Parents',
    description: 'Business trips don\'t mean missing bedtime stories. Record once, and your child hears your voice every night.',
    highlight: 'Stay connected across any distance'
  },
  {
    image: '/images/feature-bedtime-story.png',
    title: 'Peaceful Bedtime Routine',
    description: 'Create a calming bedtime ritual with personalized stories narrated in the voice your child loves most.',
    highlight: 'Better sleep, happier mornings'
  },
  {
    image: '/images/feature-voice-recording.png',
    title: 'Preserve Family Voices',
    description: 'Grandparents can record stories for grandchildren, creating treasured memories that last generations.',
    highlight: 'A gift that lasts forever'
  }
]

const stats = [
  { value: '50,000+', label: 'Families Trust Us' },
  { value: '200+', label: 'Story Templates' },
  { value: '98%', label: 'Parent Satisfaction' },
  { value: '15+', label: 'Languages Supported' }
]

const testimonials = [
  {
    quote: 'My daughter asks for "Daddy\'s stories" every night now. Even when I\'m traveling, she falls asleep to my voice.',
    author: 'Michael R.',
    role: 'Father of 2, California',
    avatar: 'M'
  },
  {
    quote: 'We recorded Grandma\'s voice before she passed. Now my kids can still hear her tell stories. It means everything to us.',
    author: 'Sarah L.',
    role: 'Mother of 3, New York',
    avatar: 'S'
  },
  {
    quote: 'The quality is incredible. My son couldn\'t tell it was AI-generated. He thinks I recorded 100 different stories!',
    author: 'David K.',
    role: 'Father, Texas',
    avatar: 'D'
  }
]
</script>

<template>
  <div class="overflow-x-hidden">
    <!-- Hero Section -->
    <section class="relative bg-gradient-hero min-h-[600px] lg:min-h-[700px] flex items-center overflow-hidden">
      <!-- Wavy decoration -->
      <svg class="absolute bottom-0 left-0 right-0 w-full" viewBox="0 0 1440 120" fill="none">
        <path
          d="M0 120L48 110C96 100 192 80 288 70C384 60 480 60 576 65C672 70 768 80 864 85C960 90 1056 90 1152 85C1248 80 1344 70 1392 65L1440 60V120H0Z"
          fill="white"
        />
      </svg>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-24">
        <div class="grid lg:grid-cols-2 gap-12 items-center">
          <!-- Left Content -->
          <div class="text-center lg:text-left">
            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight">
              Let Your Voice Tell
              <span class="block mt-2 text-sunny-400">Every Story</span>
            </h1>
            <p class="mt-6 text-lg sm:text-xl text-white/90 max-w-xl mx-auto lg:mx-0">
              Clone your voice with AI and create personalized story videos for your children.
              Let them hear your voice anytime, anywhere.
            </p>
            <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <RouterLink
                to="/studio"
                class="btn-primary text-lg px-8 py-4 bg-white text-primary-500 hover:bg-gray-50"
              >
                Start Creating
              </RouterLink>
              <RouterLink
                to="/discover"
                class="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white border-2 border-white/50 rounded-full hover:bg-white/10 transition-colors"
              >
                <svg class="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
                Browse Stories
              </RouterLink>
            </div>
          </div>

          <!-- Right Content - Device Preview -->
          <div class="hidden lg:block relative">
            <div class="relative mx-auto w-[400px]">
              <!-- Tablet Frame -->
              <div class="relative bg-gray-900 rounded-[32px] p-3 shadow-2xl">
                <div class="bg-white rounded-[24px] overflow-hidden aspect-[4/3]">
                  <img
                    src="/images/hero-family-reading.png"
                    alt="Family enjoying stories together"
                    class="w-full h-full object-cover"
                  />
                  <!-- Play Overlay -->
                  <div class="absolute inset-0 flex items-center justify-center">
                    <div class="w-20 h-20 rounded-full bg-white/90 flex items-center justify-center shadow-xl">
                      <svg class="w-8 h-8 text-primary-500 ml-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Floating elements -->
              <div class="absolute -top-4 -right-4 w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-lg animate-bounce-slow">
                <img src="/icons/icon-microphone.png" alt="" class="w-10 h-10 object-contain" />
              </div>
              <div class="absolute -bottom-4 -left-4 w-14 h-14 bg-white rounded-xl flex items-center justify-center shadow-lg animate-float">
                <img src="/icons/icon-sparkles.png" alt="" class="w-8 h-8 object-contain" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="py-20 lg:py-28 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold text-gray-900">
            Why Choose <span class="text-gradient">Echobot</span>?
          </h2>
          <p class="mt-4 text-lg text-gray-600">
            We use cutting-edge AI technology to help every family create unique story experiences
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="card text-center hover:shadow-card"
          >
            <div class="w-16 h-16 mx-auto mb-6 rounded-2xl bg-primary-50 flex items-center justify-center">
              <img :src="feature.icon" :alt="feature.title" class="w-10 h-10 object-contain" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-3">{{ feature.title }}</h3>
            <p class="text-gray-600">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Voice Cloning Detail Section -->
    <section class="py-20 lg:py-28 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div class="order-2 lg:order-1">
            <span class="inline-block px-4 py-2 bg-primary-100 text-primary-600 rounded-full text-sm font-medium mb-4">
              Voice Cloning Technology
            </span>
            <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
              Your Voice, Perfectly Recreated
            </h2>
            <p class="text-lg text-gray-600 mb-6">
              Our advanced AI only needs 30 seconds of your voice to create a natural-sounding clone.
              The technology captures your unique tone, rhythm, and warmth — everything that makes
              your voice special to your child.
            </p>
            <ul class="space-y-4 mb-8">
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">Only 30 seconds of audio needed</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">Natural emotion and intonation</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">Supports 15+ languages</span>
              </li>
            </ul>
            <RouterLink to="/studio" class="btn-primary">
              Try Voice Cloning
            </RouterLink>
          </div>
          <div class="order-1 lg:order-2">
            <div class="relative">
              <img
                src="/images/feature-voice-recording.png"
                alt="Voice Recording"
                class="rounded-2xl shadow-2xl w-full"
              />
              <div class="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-lg p-4 hidden lg:block">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                    <img src="/icons/icon-microphone.png" alt="" class="w-6 h-6" />
                  </div>
                  <div>
                    <p class="font-semibold text-gray-900">Voice Ready</p>
                    <p class="text-sm text-green-600">Clone created in 30s</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Digital Human Detail Section -->
    <section class="py-20 lg:py-28 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div>
            <div class="relative">
              <img
                src="/images/feature-digital-avatar.png"
                alt="Digital Avatar Technology"
                class="rounded-2xl shadow-2xl w-full"
              />
              <div class="absolute -bottom-6 -right-6 bg-white rounded-xl shadow-lg p-4 hidden lg:block">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                    <img src="/icons/icon-sparkles.png" alt="" class="w-6 h-6" />
                  </div>
                  <div>
                    <p class="font-semibold text-gray-900">AI Powered</p>
                    <p class="text-sm text-primary-600">Lifelike animation</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div>
            <span class="inline-block px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
              Digital Human Technology
            </span>
            <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
              Bring Stories to Life with Your Avatar
            </h2>
            <p class="text-lg text-gray-600 mb-6">
              Upload a single photo and our AI creates a lifelike digital avatar that can tell stories
              with natural facial expressions and lip sync. It's like being there in person, even when you can't be.
            </p>
            <ul class="space-y-4 mb-8">
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">One photo is all you need</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">Realistic facial expressions</span>
              </li>
              <li class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <span class="text-gray-700">Perfect lip sync with your voice</span>
              </li>
            </ul>
            <RouterLink to="/studio" class="btn-primary">
              Create Your Avatar
            </RouterLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Use Cases Section -->
    <section class="py-20 lg:py-28 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold text-gray-900">
            Perfect for Every Family Moment
          </h2>
          <p class="mt-4 text-lg text-gray-600">
            See how families around the world are using Echobot to stay connected
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="useCase in useCases"
            :key="useCase.title"
            class="bg-white rounded-2xl overflow-hidden shadow-soft hover:shadow-card transition-shadow"
          >
            <img :src="useCase.image" :alt="useCase.title" class="w-full h-48 object-cover" />
            <div class="p-6">
              <h3 class="text-xl font-bold text-gray-900 mb-3">{{ useCase.title }}</h3>
              <p class="text-gray-600 mb-4">{{ useCase.description }}</p>
              <p class="text-primary-600 font-medium text-sm">{{ useCase.highlight }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="py-16 bg-gradient-hero">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div v-for="stat in stats" :key="stat.label" class="text-center">
            <p class="text-4xl lg:text-5xl font-bold text-white mb-2">{{ stat.value }}</p>
            <p class="text-white/80">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Testimonials Section -->
    <section class="py-20 lg:py-28 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold text-gray-900">
            Loved by Families Everywhere
          </h2>
          <p class="mt-4 text-lg text-gray-600">
            Hear what parents are saying about Echobot
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="testimonial in testimonials"
            :key="testimonial.author"
            class="bg-gray-50 rounded-2xl p-6 lg:p-8"
          >
            <div class="flex gap-1 mb-4">
              <svg v-for="i in 5" :key="i" class="w-5 h-5 text-sunny-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
            </div>
            <p class="text-gray-700 mb-6 italic">"{{ testimonial.quote }}"</p>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-semibold">
                {{ testimonial.avatar }}
              </div>
              <div>
                <p class="font-semibold text-gray-900">{{ testimonial.author }}</p>
                <p class="text-sm text-gray-500">{{ testimonial.role }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Popular Stories -->
    <section class="py-20 lg:py-28 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between mb-12">
          <div>
            <h2 class="text-3xl sm:text-4xl font-bold text-gray-900">
              Popular Stories
            </h2>
            <p class="mt-2 text-gray-600">
              Handpicked stories waiting for your voice
            </p>
          </div>
          <RouterLink
            to="/discover"
            class="hidden sm:inline-flex items-center text-primary-500 font-medium hover:text-primary-600"
          >
            View All
            <svg class="w-5 h-5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </RouterLink>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div
            v-for="i in 4"
            :key="i"
            class="animate-pulse"
          >
            <div class="bg-gray-200 rounded-2xl aspect-[4/3]"></div>
            <div class="mt-4 h-4 bg-gray-200 rounded w-3/4"></div>
            <div class="mt-2 h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>

        <!-- Story Grid -->
        <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StoryCard
            v-for="story in stories.slice(0, 8)"
            :key="story.id"
            :story="story"
          />
        </div>

        <div class="text-center mt-8 sm:hidden">
          <RouterLink to="/discover" class="btn-secondary">
            View All Stories
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 lg:py-28 bg-gradient-hero relative overflow-hidden">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">
          Your Voice, Their Favorite Stories
        </h2>
        <p class="mt-6 text-lg text-white/90 max-w-2xl mx-auto">
          Whether you're traveling for work or busy with life, you can still tell bedtime stories
          to your children with your own voice. Love knows no distance.
        </p>
        <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <RouterLink
            to="/register"
            class="btn-primary text-lg px-10 py-4 bg-white text-primary-500 hover:bg-gray-50"
          >
            Get Started Free
          </RouterLink>
          <RouterLink
            to="/discover"
            class="inline-flex items-center justify-center px-10 py-4 text-lg font-semibold text-white border-2 border-white rounded-full hover:bg-white/10 transition-colors"
          >
            Learn More
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>
