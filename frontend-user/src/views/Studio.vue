<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { storyApi, voiceCloneApi, digitalHumanApi, storyGenerationApi } from '@/api'
import type { Story, VoiceProfile, AvatarProfile } from '@/types'

const route = useRoute()

const currentStep = ref(1)

const stories = ref<Story[]>([])
const selectedStory = ref<Story | null>(null)
const storiesLoading = ref(false)

const voiceProfiles = ref<VoiceProfile[]>([])
const selectedVoiceProfile = ref<VoiceProfile | null>(null)
const audioBlob = ref<Blob | null>(null)
const voicePreviewUrl = ref('')

const avatarProfiles = ref<AvatarProfile[]>([])
const selectedAvatarProfile = ref<AvatarProfile | null>(null)
const uploadedImage = ref<File | null>(null)
const imagePreviewUrl = ref('')

const generating = ref(false)
const progress = ref(0)
const currentTask = ref('')
const resultVideoUrl = ref('')

const steps = [
  { number: '1', title: 'Choose Story', icon: '/icons/icon-storybook.png' },
  { number: '2', title: 'Upload Voice', icon: '/icons/icon-microphone.png' },
  { number: '3', title: 'Upload Photo', icon: '/icons/icon-avatar.png' },
  { number: '4', title: 'Generate', icon: '/icons/icon-sparkles.png' }
]

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: return !!selectedStory.value
    case 2: return !!selectedVoiceProfile.value
    case 3: return !!selectedAvatarProfile.value
    default: return false
  }
})

const loadStories = async () => {
  storiesLoading.value = true
  try {
    const res = await storyApi.getStories({ page_size: 20 })
    stories.value = res.data.items
  } finally {
    storiesLoading.value = false
  }
}

const loadVoiceProfiles = async () => {
  try {
    const res = await voiceCloneApi.getProfiles()
    voiceProfiles.value = res.data.profiles
  } catch (e) {
    console.error('Failed to load voice profiles:', e)
  }
}

const loadAvatarProfiles = async () => {
  try {
    const res = await digitalHumanApi.getProfiles()
    avatarProfiles.value = res.data.profiles
  } catch (e) {
    console.error('Failed to load avatar profiles:', e)
  }
}

const nextStep = () => {
  if (currentStep.value < 4 && canProceed.value) {
    currentStep.value++
    if (currentStep.value === 2) loadVoiceProfiles()
    if (currentStep.value === 3) loadAvatarProfiles()
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const handleAudioUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    audioBlob.value = file
    voicePreviewUrl.value = URL.createObjectURL(file)
  }
}

const handleImageUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadedImage.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)
  }
}

const startGeneration = async () => {
  if (!selectedStory.value || !selectedVoiceProfile.value || !selectedAvatarProfile.value) return

  generating.value = true
  progress.value = 0
  currentTask.value = 'Preparing...'

  try {
    const res = await storyGenerationApi.createJob({
      story_id: selectedStory.value.id,
      voice_profile_id: selectedVoiceProfile.value.id,
      avatar_profile_id: selectedAvatarProfile.value.id,
      full_video: true
    })

    const jobId = res.data.id
    const pollStatus = async () => {
      const statusRes = await storyGenerationApi.getJob(jobId)
      const job = statusRes.data
      progress.value = job.progress
      currentTask.value = job.current_step

      if (job.status === 'completed') {
        resultVideoUrl.value = job.output_video_url || ''
        generating.value = false
      } else if (job.status === 'failed') {
        alert('Generation failed: ' + job.error)
        generating.value = false
      } else {
        setTimeout(pollStatus, 2000)
      }
    }
    pollStatus()
  } catch (e) {
    console.error('Failed to start generation:', e)
    generating.value = false
    alert('Failed to start generation')
  }
}

loadStories()

if (route.query.story_id) {
  storyApi.getStory(route.query.story_id as string).then(res => {
    selectedStory.value = res.data
  })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gray-900">AI Studio</h1>
        <p class="mt-2 text-gray-600">Create stories with your voice and avatar</p>
      </div>

      <!-- Steps Indicator -->
      <div class="flex items-center justify-center mb-12">
        <div class="flex items-center gap-4">
          <template v-for="(step, index) in steps" :key="step.number">
            <div class="flex items-center">
              <div
                :class="[
                  'w-12 h-12 rounded-full flex items-center justify-center transition-all',
                  currentStep >= step.number
                    ? 'bg-primary-500 shadow-lg'
                    : 'bg-gray-200'
                ]"
              >
                <img :src="step.icon" alt="" class="w-6 h-6 object-contain" />
              </div>
              <span
                :class="[
                  'ml-2 font-medium hidden sm:block',
                  currentStep >= step.number ? 'text-primary-500' : 'text-gray-400'
                ]"
              >
                {{ step.title }}
              </span>
            </div>
            <div
              v-if="index < steps.length - 1"
              :class="[
                'w-12 lg:w-24 h-1 rounded-full mx-2',
                currentStep > step.number ? 'bg-primary-500' : 'bg-gray-200'
              ]"
            ></div>
          </template>
        </div>
      </div>

      <div class="bg-white rounded-3xl shadow-soft p-6 lg:p-10">
        <!-- Step 1: Select Story -->
        <div v-if="currentStep === 1">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Choose a Story</h2>

          <div v-if="storiesLoading" class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div v-for="i in 6" :key="i" class="animate-pulse">
              <div class="bg-gray-200 rounded-xl aspect-[4/3]"></div>
              <div class="mt-2 h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>

          <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div
              v-for="story in stories"
              :key="story.id"
              @click="selectedStory = story"
              :class="[
                'relative rounded-xl overflow-hidden cursor-pointer transition-all border-2',
                selectedStory?.id === story.id
                  ? 'border-primary-500 ring-4 ring-primary-100'
                  : 'border-transparent hover:border-gray-200'
              ]"
            >
              <img
                :src="story.thumbnail_url"
                :alt="story.title"
                class="w-full aspect-[4/3] object-cover"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
              <div class="absolute bottom-0 left-0 right-0 p-3">
                <h3 class="text-white font-medium text-sm line-clamp-2">{{ story.title_en || story.title }}</h3>
              </div>
              <div
                v-if="selectedStory?.id === story.id"
                class="absolute top-2 right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center"
              >
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Voice -->
        <div v-else-if="currentStep === 2">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Select or Upload Voice</h2>

          <div v-if="voiceProfiles.length > 0" class="mb-8">
            <h3 class="text-sm font-medium text-gray-500 mb-3">My Voice Profiles</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div
                v-for="profile in voiceProfiles"
                :key="profile.id"
                @click="selectedVoiceProfile = profile"
                :class="[
                  'p-4 rounded-xl border-2 cursor-pointer transition-all',
                  selectedVoiceProfile?.id === profile.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                ]"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                    <img src="/icons/icon-microphone.png" alt="" class="w-5 h-5 object-contain" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-gray-900 truncate">{{ profile.name }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
            <div class="w-16 h-16 mx-auto mb-4 bg-primary-50 rounded-full flex items-center justify-center">
              <img src="/icons/icon-microphone.png" alt="" class="w-8 h-8 object-contain" />
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Upload New Voice Sample</h3>
            <p class="text-gray-500 text-sm mb-4">Upload a clear audio recording (30+ seconds)</p>
            <label class="btn-secondary cursor-pointer">
              <input
                type="file"
                accept="audio/*"
                class="hidden"
                @change="handleAudioUpload"
              />
              Choose Audio File
            </label>
            <div v-if="voicePreviewUrl" class="mt-4">
              <audio :src="voicePreviewUrl" controls class="w-full max-w-md mx-auto"></audio>
            </div>
          </div>
        </div>

        <!-- Step 3: Avatar -->
        <div v-else-if="currentStep === 3">
          <h2 class="text-xl font-bold text-gray-900 mb-6">Select or Upload Photo</h2>

          <div v-if="avatarProfiles.length > 0" class="mb-8">
            <h3 class="text-sm font-medium text-gray-500 mb-3">My Avatar Profiles</h3>
            <div class="grid grid-cols-3 md:grid-cols-4 gap-4">
              <div
                v-for="profile in avatarProfiles"
                :key="profile.id"
                @click="selectedAvatarProfile = profile"
                :class="[
                  'relative rounded-xl overflow-hidden cursor-pointer transition-all border-2',
                  selectedAvatarProfile?.id === profile.id
                    ? 'border-primary-500 ring-4 ring-primary-100'
                    : 'border-transparent hover:border-gray-200'
                ]"
              >
                <img
                  :src="profile.image_url"
                  :alt="profile.name"
                  class="w-full aspect-square object-cover"
                />
                <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/50">
                  <p class="text-white text-xs text-center truncate">{{ profile.name }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
            <div class="w-16 h-16 mx-auto mb-4 bg-primary-50 rounded-full flex items-center justify-center">
              <img src="/icons/icon-camera.png" alt="" class="w-8 h-8 object-contain" />
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Upload New Photo</h3>
            <p class="text-gray-500 text-sm mb-4">Upload a clear front-facing photo</p>
            <label class="btn-secondary cursor-pointer">
              <input
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleImageUpload"
              />
              Choose Image
            </label>
            <div v-if="imagePreviewUrl" class="mt-4">
              <img :src="imagePreviewUrl" class="w-32 h-32 mx-auto rounded-xl object-cover" />
            </div>
          </div>
        </div>

        <!-- Step 4: Generate -->
        <div v-else-if="currentStep === 4">
          <div v-if="!generating && !resultVideoUrl">
            <h2 class="text-xl font-bold text-gray-900 mb-6">Review & Generate</h2>

            <div class="space-y-4 mb-8">
              <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                <img
                  :src="selectedStory?.thumbnail_url"
                  class="w-16 h-16 rounded-lg object-cover"
                />
                <div>
                  <p class="text-sm text-gray-500">Story</p>
                  <p class="font-medium text-gray-900">{{ selectedStory?.title_en || selectedStory?.title }}</p>
                </div>
              </div>

              <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                <div class="w-16 h-16 rounded-lg bg-primary-100 flex items-center justify-center">
                  <img src="/icons/icon-microphone.png" alt="" class="w-8 h-8 object-contain" />
                </div>
                <div>
                  <p class="text-sm text-gray-500">Voice</p>
                  <p class="font-medium text-gray-900">{{ selectedVoiceProfile?.name }}</p>
                </div>
              </div>

              <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                <img
                  :src="selectedAvatarProfile?.image_url"
                  class="w-16 h-16 rounded-lg object-cover"
                />
                <div>
                  <p class="text-sm text-gray-500">Avatar</p>
                  <p class="font-medium text-gray-900">{{ selectedAvatarProfile?.name }}</p>
                </div>
              </div>
            </div>

            <button
              @click="startGeneration"
              class="btn-primary w-full py-4 text-lg"
            >
              Start Generation
            </button>
          </div>

          <div v-else-if="generating" class="text-center py-12">
            <div class="w-24 h-24 mx-auto mb-6 relative">
              <div class="absolute inset-0 rounded-full border-4 border-gray-200"></div>
              <div
                class="absolute inset-0 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"
              ></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-2xl font-bold text-primary-500">{{ progress }}%</span>
              </div>
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Generating...</h3>
            <p class="text-gray-500">{{ currentTask }}</p>
            <div class="mt-8 max-w-md mx-auto">
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-primary-500 rounded-full transition-all duration-500"
                  :style="{ width: `${progress}%` }"
                ></div>
              </div>
            </div>
          </div>

          <div v-else-if="resultVideoUrl" class="text-center">
            <div class="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Generation Complete!</h3>
            <p class="text-gray-500 mb-6">Your personalized story video is ready</p>

            <video
              :src="resultVideoUrl"
              controls
              class="w-full max-w-2xl mx-auto rounded-xl shadow-lg mb-6"
            ></video>

            <div class="flex gap-4 justify-center">
              <a
                :href="resultVideoUrl"
                download
                class="btn-primary"
              >
                Download Video
              </a>
              <button
                @click="currentStep = 1; resultVideoUrl = ''"
                class="btn-secondary"
              >
                Create Another
              </button>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div v-if="currentStep < 4 || (!generating && !resultVideoUrl)" class="flex justify-between mt-8 pt-6 border-t">
          <button
            v-if="currentStep > 1"
            @click="prevStep"
            class="btn-secondary"
          >
            Previous
          </button>
          <div v-else></div>

          <button
            v-if="currentStep < 4"
            @click="nextStep"
            :disabled="!canProceed"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
