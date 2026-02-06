<script setup lang="ts">
// Shopify Integration - Coming Soon
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4">
    <div class="text-center max-w-lg">
      <!-- Shopify Icon -->
      <div class="w-24 h-24 mx-auto mb-8 rounded-2xl bg-[#95BF47] flex items-center justify-center shadow-lg">
        <svg class="w-14 h-14 text-white" viewBox="0 0 109 124" fill="currentColor">
          <path d="M94.784 23.585c-.099-.63-.559-1.036-1.119-1.085-.56-.05-11.37-.854-11.37-.854s-7.543-7.414-8.379-8.243c-.837-.829-2.472-.58-3.107-.39-.014 0-1.677.518-4.485 1.382-2.669-7.7-7.378-14.757-15.662-14.757-.229 0-.463.01-.699.025C47.782-2.587 45.224 0 43.073 0c-19.389 0-28.66 24.238-31.574 36.559-7.574 2.342-12.957 4.003-13.621 4.217C-5.27 41.887-5.4 42.017-5.6 44.752-5.74 46.986-15.558 122.164-15.558 122.164L75.162 124l39.232-8.475S94.883 24.215 94.784 23.585zM66.393 15.478c-2.119.656-4.531 1.404-7.166 2.22v-1.608c0-4.91-.679-8.876-1.769-11.96 4.379.554 7.305 5.544 8.935 11.348zM51.57 5.167c1.239 2.989 2.045 7.25 2.045 13.049v.8c-4.673 1.448-9.771 3.024-14.88 4.604C42.029 12.22 47.105 6.35 51.57 5.167zM43.439 1.591c.699 0 1.377.234 2.025.69-5.879 2.762-12.186 9.727-14.836 23.652-4.074 1.26-8.068 2.497-11.798 3.651C22.478 19.134 30.264 1.591 43.439 1.591z"/>
          <path d="M93.665 22.5c-.56-.05-11.37-.854-11.37-.854s-7.543-7.414-8.379-8.243c-.31-.307-.729-.473-1.177-.55v109.43l39.232-8.475S94.883 24.215 94.784 23.585c-.099-.63-.559-1.036-1.119-1.085z" fill-opacity="0.25"/>
        </svg>
      </div>

      <!-- Title -->
      <h1 class="text-3xl font-bold text-gray-900 mb-4">
        Shopify Integration
      </h1>

      <!-- Description -->
      <p class="text-lg text-gray-600 mb-8 leading-relaxed">
        We're building an exciting Shopify integration that will allow you to create personalized story videos for your e-commerce store. Stay tuned!
      </p>

      <!-- Coming Soon Badge -->
      <div class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-full">
        <span class="relative flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
        </span>
        <span class="font-semibold text-green-700">Coming Soon</span>
      </div>

      <!-- Features Preview -->
      <div class="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="p-4 bg-gray-50 rounded-xl">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 text-sm">Quick Integration</h3>
          <p class="text-xs text-gray-500 mt-1">One-click setup with your store</p>
        </div>
        <div class="p-4 bg-gray-50 rounded-xl">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 text-sm">Product Videos</h3>
          <p class="text-xs text-gray-500 mt-1">AI-generated product showcases</p>
        </div>
        <div class="p-4 bg-gray-50 rounded-xl">
          <div class="w-10 h-10 mx-auto mb-3 bg-primary-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <h3 class="font-semibold text-gray-900 text-sm">Analytics</h3>
          <p class="text-xs text-gray-500 mt-1">Track engagement metrics</p>
        </div>
      </div>

      <!-- Back Button -->
      <div class="mt-10">
        <RouterLink to="/discover" class="text-primary-500 hover:text-primary-600 font-medium">
          Browse Stories
        </RouterLink>
      </div>
    </div>
  </div>
</template>
