<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'sky' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  block?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false
})

const classes = computed(() => {
  const base = 'inline-flex items-center justify-center font-semibold rounded-full transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-primary-500 text-white shadow-button hover:bg-primary-600 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0',
    secondary: 'bg-white text-primary-500 border-2 border-primary-500 hover:bg-primary-50',
    sky: 'bg-sky-500 text-white shadow-lg hover:bg-sky-600 hover:-translate-y-0.5',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100'
  }

  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  }

  return [
    base,
    variants[props.variant],
    sizes[props.size],
    props.block ? 'w-full' : ''
  ]
})
</script>

<template>
  <button
    :class="classes"
    :disabled="disabled || loading"
  >
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    <slot />
  </button>
</template>

<script lang="ts">
import { computed } from 'vue'
</script>
