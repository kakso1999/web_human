<script setup lang="ts">
const currentYear = new Date().getFullYear()

const footerLinks = [
  {
    title: 'Product',
    links: [
      { name: 'Discover Stories', path: '/discover' },
      { name: 'AI Studio', path: '/studio' },
      { name: 'Audiobook', path: '/audiobook' },
    ]
  },
  {
    title: 'Support',
    links: [
      { name: 'Help Center', path: '/help' },
      { name: 'Contact Us', path: '/contact' },
      { name: 'FAQ', path: '/faq' },
    ]
  },
  {
    title: 'Company',
    links: [
      { name: 'About Us', path: '/about' },
      { name: 'Privacy Policy', path: '/privacy' },
      { name: 'Terms of Service', path: '/terms' },
    ]
  }
]
</script>

<template>
  <footer class="bg-gray-50 border-t">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
        <!-- Brand -->
        <div class="col-span-2 md:col-span-1">
          <RouterLink to="/" class="flex items-center gap-2">
            <img src="/logo2.jpg" alt="Echobot" class="h-10 rounded-lg" />
          </RouterLink>
          <p class="mt-4 text-gray-600 text-sm leading-relaxed">
            Let your voice tell every story. AI-powered platform bringing family moments to life.
          </p>
          <!-- Social Links -->
          <div class="flex gap-4 mt-6">
            <a
              href="#"
              class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-primary-100 hover:text-primary-500 transition-colors"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </a>
            <a
              href="#"
              class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-primary-100 hover:text-primary-500 transition-colors"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
              </svg>
            </a>
          </div>
        </div>

        <!-- Links -->
        <div
          v-for="section in footerLinks"
          :key="section.title"
        >
          <h4 class="font-semibold text-gray-900 mb-4">{{ section.title }}</h4>
          <ul class="space-y-3">
            <li v-for="link in section.links" :key="link.path">
              <RouterLink
                :to="link.path"
                class="text-gray-600 hover:text-primary-500 transition-colors text-sm"
              >
                {{ link.name }}
              </RouterLink>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom -->
      <div class="mt-12 pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
        <p class="text-gray-500 text-sm">
          &copy; {{ currentYear }} Echobot. All rights reserved.
        </p>
        <div class="flex items-center gap-6">
          <RouterLink to="/privacy" class="text-gray-500 hover:text-gray-700 text-sm">
            Privacy Policy
          </RouterLink>
          <RouterLink to="/terms" class="text-gray-500 hover:text-gray-700 text-sm">
            Terms of Service
          </RouterLink>
        </div>
      </div>
    </div>
  </footer>
</template>
