<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Contact Us</h1>
      <p class="text-gray-600 mb-8">We'd love to hear from you. Send us a message and we'll respond as soon as possible.</p>

      <div class="bg-white rounded-2xl shadow-soft p-6 mb-8">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input
              v-model="form.name"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Your name"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Subject</label>
            <select
              v-model="form.subject"
              class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Select a topic</option>
              <option value="general">General Inquiry</option>
              <option value="technical">Technical Support</option>
              <option value="billing">Billing Question</option>
              <option value="feedback">Feedback</option>
              <option value="partnership">Partnership</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Message</label>
            <textarea
              v-model="form.message"
              rows="5"
              required
              class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              placeholder="How can we help you?"
            ></textarea>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full btn-primary py-3"
          >
            {{ submitting ? 'Sending...' : 'Send Message' }}
          </button>
        </form>

        <div v-if="submitted" class="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700">
          Thank you for your message! We'll get back to you within 24-48 hours.
        </div>
      </div>

      <!-- Contact Info -->
      <div class="grid md:grid-cols-3 gap-6">
        <div class="bg-white rounded-2xl shadow-soft p-6 text-center">
          <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 mb-1">Email</h3>
          <p class="text-sm text-gray-600">support@echobot.ai</p>
        </div>

        <div class="bg-white rounded-2xl shadow-soft p-6 text-center">
          <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 mb-1">Live Chat</h3>
          <p class="text-sm text-gray-600">Mon-Fri, 9am-6pm</p>
        </div>

        <div class="bg-white rounded-2xl shadow-soft p-6 text-center">
          <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-primary-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 mb-1">Twitter</h3>
          <p class="text-sm text-gray-600">@echobot_ai</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

const form = reactive({
  name: '',
  email: '',
  subject: '',
  message: ''
})

const submitting = ref(false)
const submitted = ref(false)

const handleSubmit = async () => {
  submitting.value = true
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 1500))
  submitting.value = false
  submitted.value = true
  // Reset form
  form.name = ''
  form.email = ''
  form.subject = ''
  form.message = ''
}
</script>
