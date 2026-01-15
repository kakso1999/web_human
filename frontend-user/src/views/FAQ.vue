<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Frequently Asked Questions</h1>
      <p class="text-gray-600 mb-8">Find answers to common questions about Echobot.</p>

      <!-- FAQ Categories -->
      <div class="flex flex-wrap gap-2 mb-8">
        <button
          v-for="cat in categories"
          :key="cat"
          @click="activeCategory = cat"
          class="px-4 py-2 rounded-full text-sm font-medium transition-colors"
          :class="activeCategory === cat ? 'bg-primary-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'"
        >
          {{ cat }}
        </button>
      </div>

      <!-- FAQ Items -->
      <div class="space-y-4">
        <div
          v-for="(faq, index) in filteredFaqs"
          :key="index"
          class="bg-white rounded-2xl shadow-soft overflow-hidden"
        >
          <button
            @click="toggleFaq(index)"
            class="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <span class="font-medium text-gray-900">{{ faq.question }}</span>
            <svg
              class="w-5 h-5 text-gray-500 transform transition-transform"
              :class="{ 'rotate-180': openFaqs.includes(index) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            v-show="openFaqs.includes(index)"
            class="px-6 pb-4 text-gray-600"
          >
            {{ faq.answer }}
          </div>
        </div>
      </div>

      <!-- Still have questions -->
      <div class="mt-12 text-center bg-white rounded-2xl shadow-soft p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Still have questions?</h3>
        <p class="text-gray-600 mb-4">Can't find the answer you're looking for? Please chat with our friendly team.</p>
        <RouterLink to="/contact" class="btn-primary inline-block">
          Get in Touch
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const categories = ['All', 'Getting Started', 'Voice Cloning', 'Billing', 'Technical']
const activeCategory = ref('All')
const openFaqs = ref<number[]>([])

const faqs = [
  {
    category: 'Getting Started',
    question: 'What is Echobot?',
    answer: 'Echobot is an AI-powered platform that allows you to create personalized stories using voice cloning technology. You can record your voice or upload audio samples, and our AI will generate stories narrated in your voice or any voice profile you create.'
  },
  {
    category: 'Getting Started',
    question: 'How do I get started?',
    answer: 'Simply create an account, record a voice sample (at least 10 seconds), and start generating stories! Our platform will guide you through the process step by step.'
  },
  {
    category: 'Voice Cloning',
    question: 'How long does voice cloning take?',
    answer: 'Voice profile creation typically takes 1-3 minutes depending on the audio length. Story generation with your cloned voice takes 2-5 minutes for most stories.'
  },
  {
    category: 'Voice Cloning',
    question: 'What audio quality do I need for voice cloning?',
    answer: 'For best results, record in a quiet environment using a good microphone. We recommend at least 10-30 seconds of clear speech without background noise. The higher the quality of your input, the better the cloned voice will sound.'
  },
  {
    category: 'Voice Cloning',
    question: 'Can I create multiple voice profiles?',
    answer: 'Yes! Free users can create up to 5 voice profiles. Basic plan users get 20 profiles, and Premium users have unlimited voice profiles.'
  },
  {
    category: 'Billing',
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and Apple Pay. All payments are processed securely through Stripe.'
  },
  {
    category: 'Billing',
    question: 'Can I cancel my subscription anytime?',
    answer: 'Yes, you can cancel your subscription at any time from your account settings. Your plan will remain active until the end of your current billing period.'
  },
  {
    category: 'Billing',
    question: 'Do you offer refunds?',
    answer: 'We offer a 7-day money-back guarantee for new subscribers. If you\'re not satisfied with our service, contact support within 7 days of your first payment for a full refund.'
  },
  {
    category: 'Technical',
    question: 'What file formats are supported?',
    answer: 'For audio uploads, we support MP3, WAV, M4A, and OGG formats. For avatar photos, we accept JPG, PNG, and WEBP. Generated videos are exported in MP4 format.'
  },
  {
    category: 'Technical',
    question: 'Is my data secure?',
    answer: 'Yes, we take security seriously. All data is encrypted in transit and at rest. Voice samples and personal information are stored securely and never shared with third parties. You can delete your data at any time from your account settings.'
  }
]

const filteredFaqs = computed(() => {
  if (activeCategory.value === 'All') return faqs
  return faqs.filter(faq => faq.category === activeCategory.value)
})

const toggleFaq = (index: number) => {
  const i = openFaqs.value.indexOf(index)
  if (i > -1) {
    openFaqs.value.splice(i, 1)
  } else {
    openFaqs.value.push(index)
  }
}
</script>
