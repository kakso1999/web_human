<script setup lang="ts">
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center">
    <div class="text-center">
      <div class="w-32 h-32 mx-auto mb-8 bg-primary-50 rounded-full flex items-center justify-center">
        <img src="/icons/icon-search.png" alt="" class="w-16 h-16 object-contain" />
      </div>
      <h1 class="text-4xl font-bold text-gray-900 mb-4">404</h1>
      <p class="text-xl text-gray-600 mb-8">Page Not Found</p>
      <div class="flex gap-4 justify-center">
        <RouterLink to="/" class="btn-primary">
          Back to Home
        </RouterLink>
        <RouterLink to="/discover" class="btn-secondary">
          Browse Stories
        </RouterLink>
      </div>
    </div>
  </div>
</template>
