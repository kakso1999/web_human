<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { voiceCloneApi, digitalHumanApi } from '@/api'
import type { PresetStory, VoiceProfile } from '@/types'

const router = useRouter()

// 档案类型选择
type ProfileType = 'voice' | 'avatar' | null
const profileType = ref<ProfileType>(null)

// 当前步骤
const currentStep = ref(1)

// ==================== 声音档案相关 ====================
const presetStories = ref<PresetStory[]>([])
const selectedStoryId = ref('')
const audioFile = ref<File | null>(null)
const audioPreviewUrl = ref('')
const voiceTaskId = ref('')
const voiceTaskStatus = ref('')
const voiceTaskProgress = ref(0)
const voicePreviewAudioUrl = ref('')
const voiceProfileName = ref('')
const voiceCreating = ref(false)
const voiceSaving = ref(false)

// ==================== 数字人档案相关 ====================
const voiceProfiles = ref<VoiceProfile[]>([])
const selectedVoiceProfileId = ref('')
const imageFile = ref<File | null>(null)
const imagePreviewUrl = ref('')
const avatarTaskId = ref('')
const avatarTaskStatus = ref('')
const avatarTaskProgress = ref(0)
const avatarPreviewVideoUrl = ref('')
const avatarProfileName = ref('')
const avatarCreating = ref(false)
const avatarSaving = ref(false)

// 步骤配置
const voiceSteps = [
  { number: 1, title: 'Upload Audio', description: 'Record or upload your voice' },
  { number: 2, title: 'Select Story', description: 'Choose a preview story' },
  { number: 3, title: 'Create & Save', description: 'Preview and save profile' }
]

const avatarSteps = [
  { number: 1, title: 'Upload Photo', description: 'Upload a clear face photo' },
  { number: 2, title: 'Select Voice', description: 'Choose a voice (optional)' },
  { number: 3, title: 'Create & Save', description: 'Preview and save profile' }
]

const steps = computed(() => profileType.value === 'voice' ? voiceSteps : avatarSteps)

// 能否进入下一步
const canProceed = computed(() => {
  if (profileType.value === 'voice') {
    switch (currentStep.value) {
      case 1: return !!audioFile.value
      case 2: return !!selectedStoryId.value
      case 3: return voiceTaskStatus.value === 'completed' && !!voiceProfileName.value.trim()
      default: return false
    }
  } else if (profileType.value === 'avatar') {
    switch (currentStep.value) {
      case 1: return !!imageFile.value
      case 2: return true // 声音是可选的
      case 3: return avatarTaskStatus.value === 'completed' && !!avatarProfileName.value.trim()
      default: return false
    }
  }
  return false
})

// 加载预设故事
const loadPresetStories = async () => {
  try {
    const res = await voiceCloneApi.getPresetStories()
    presetStories.value = res.data.stories
    if (presetStories.value.length > 0) {
      selectedStoryId.value = presetStories.value[0].id
    }
  } catch (e) {
    console.error('Failed to load preset stories:', e)
  }
}

// 加载声音档案
const loadVoiceProfiles = async () => {
  try {
    const res = await voiceCloneApi.getProfiles()
    voiceProfiles.value = res.data.profiles
  } catch (e) {
    console.error('Failed to load voice profiles:', e)
  }
}

// 处理音频上传
const handleAudioUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    audioFile.value = file
    audioPreviewUrl.value = URL.createObjectURL(file)
  }
}

// 处理图片上传
const handleImageUpload = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    imageFile.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)
  }
}

// 下一步
const nextStep = () => {
  if (currentStep.value < 3 && canProceed.value) {
    currentStep.value++

    // 进入最后一步时，自动开始创建任务
    if (currentStep.value === 3) {
      if (profileType.value === 'voice') {
        createVoicePreview()
      } else {
        createAvatarPreview()
      }
    }
  }
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// 创建声音克隆预览
const createVoicePreview = async () => {
  if (!audioFile.value || !selectedStoryId.value) return

  voiceCreating.value = true
  voiceTaskStatus.value = 'processing'
  voiceTaskProgress.value = 0

  try {
    const res = await voiceCloneApi.createPreview(audioFile.value, selectedStoryId.value)
    voiceTaskId.value = res.data.task_id

    // 轮询任务状态
    pollVoiceTask()
  } catch (e: any) {
    console.error('Failed to create voice preview:', e)
    voiceTaskStatus.value = 'failed'
    voiceCreating.value = false
    alert(e.response?.data?.detail || 'Failed to create voice preview')
  }
}

// 轮询声音克隆任务
const pollVoiceTask = async () => {
  if (!voiceTaskId.value) return

  try {
    const res = await voiceCloneApi.getPreviewStatus(voiceTaskId.value)
    voiceTaskStatus.value = res.data.status
    voiceTaskProgress.value = res.data.progress || 0

    if (res.data.status === 'completed') {
      voicePreviewAudioUrl.value = res.data.audio_url || ''
      voiceCreating.value = false
    } else if (res.data.status === 'failed') {
      voiceCreating.value = false
      alert('Voice cloning failed: ' + (res.data.error || 'Unknown error'))
    } else {
      // 继续轮询
      setTimeout(pollVoiceTask, 2000)
    }
  } catch (e) {
    console.error('Failed to poll voice task:', e)
    voiceCreating.value = false
  }
}

// 保存声音档案
const saveVoiceProfile = async () => {
  if (!voiceTaskId.value || !voiceProfileName.value.trim()) return

  voiceSaving.value = true
  try {
    await voiceCloneApi.saveProfile(voiceTaskId.value, voiceProfileName.value.trim())
    alert('Voice profile saved successfully!')
    router.push('/profiles/voice')
  } catch (e: any) {
    console.error('Failed to save voice profile:', e)
    alert(e.response?.data?.detail || 'Failed to save voice profile')
  } finally {
    voiceSaving.value = false
  }
}

// 创建数字人预览
const createAvatarPreview = async () => {
  if (!imageFile.value) return

  avatarCreating.value = true
  avatarTaskStatus.value = 'processing'
  avatarTaskProgress.value = 0

  try {
    const options: any = {}
    if (selectedVoiceProfileId.value) {
      options.voice_profile_id = selectedVoiceProfileId.value
    }

    const res = await digitalHumanApi.createPreview(imageFile.value, options)
    avatarTaskId.value = res.data.task_id

    // 轮询任务状态
    pollAvatarTask()
  } catch (e: any) {
    console.error('Failed to create avatar preview:', e)
    avatarTaskStatus.value = 'failed'
    avatarCreating.value = false
    alert(e.response?.data?.detail || 'Failed to create avatar preview')
  }
}

// 轮询数字人任务
const pollAvatarTask = async () => {
  if (!avatarTaskId.value) return

  try {
    const res = await digitalHumanApi.getPreviewStatus(avatarTaskId.value)
    avatarTaskStatus.value = res.data.status
    avatarTaskProgress.value = res.data.progress || 0

    if (res.data.status === 'completed') {
      avatarPreviewVideoUrl.value = res.data.video_url || ''
      avatarCreating.value = false
    } else if (res.data.status === 'failed') {
      avatarCreating.value = false
      alert('Avatar creation failed: ' + (res.data.error || 'Unknown error'))
    } else {
      // 继续轮询
      setTimeout(pollAvatarTask, 2000)
    }
  } catch (e) {
    console.error('Failed to poll avatar task:', e)
    avatarCreating.value = false
  }
}

// 保存数字人档案
const saveAvatarProfile = async () => {
  if (!avatarTaskId.value || !avatarProfileName.value.trim()) return

  avatarSaving.value = true
  try {
    await digitalHumanApi.saveProfile(avatarTaskId.value, avatarProfileName.value.trim())
    alert('Avatar profile saved successfully!')
    router.push('/profiles/avatar')
  } catch (e: any) {
    console.error('Failed to save avatar profile:', e)
    alert(e.response?.data?.detail || 'Failed to save avatar profile')
  } finally {
    avatarSaving.value = false
  }
}

// 选择档案类型
const selectProfileType = (type: ProfileType) => {
  profileType.value = type
  currentStep.value = 1

  if (type === 'voice') {
    loadPresetStories()
  } else if (type === 'avatar') {
    loadVoiceProfiles()
  }
}

// 返回选择类型
const backToTypeSelection = () => {
  profileType.value = null
  currentStep.value = 1
  // 重置所有状态
  audioFile.value = null
  audioPreviewUrl.value = ''
  imageFile.value = null
  imagePreviewUrl.value = ''
  voiceTaskId.value = ''
  voiceTaskStatus.value = ''
  avatarTaskId.value = ''
  avatarTaskStatus.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gray-900">Create Profile</h1>
        <p class="mt-2 text-gray-600">Create voice or avatar profiles to personalize your stories</p>
      </div>

      <!-- 类型选择 -->
      <div v-if="!profileType" class="max-w-2xl mx-auto">
        <h2 class="text-xl font-semibold text-gray-900 text-center mb-8">What would you like to create?</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 声音档案 -->
          <div
            @click="selectProfileType('voice')"
            class="bg-white rounded-2xl p-8 shadow-soft cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1 border-2 border-transparent hover:border-primary-200"
          >
            <div class="w-20 h-20 mx-auto mb-6 bg-primary-100 rounded-2xl flex items-center justify-center">
              <svg class="w-10 h-10 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 text-center mb-2">Voice Profile</h3>
            <p class="text-gray-500 text-center text-sm">Clone your voice to narrate stories in your own voice</p>
            <div class="mt-6 flex justify-center">
              <span class="inline-flex items-center px-4 py-2 bg-primary-50 text-primary-600 rounded-full text-sm font-medium">
                Upload Audio
                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
            </div>
          </div>

          <!-- 数字人档案 -->
          <div
            @click="selectProfileType('avatar')"
            class="bg-white rounded-2xl p-8 shadow-soft cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1 border-2 border-transparent hover:border-primary-200"
          >
            <div class="w-20 h-20 mx-auto mb-6 bg-blue-100 rounded-2xl flex items-center justify-center">
              <svg class="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 text-center mb-2">Avatar Profile</h3>
            <p class="text-gray-500 text-center text-sm">Create a digital avatar from your photo</p>
            <div class="mt-6 flex justify-center">
              <span class="inline-flex items-center px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm font-medium">
                Upload Photo
                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤向导 -->
      <template v-else>
        <!-- 返回按钮 -->
        <button
          @click="backToTypeSelection"
          class="mb-6 flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          Back to selection
        </button>

        <!-- 步骤指示器 -->
        <div class="flex items-center justify-center mb-10">
          <div class="flex items-center gap-4">
            <template v-for="(step, index) in steps" :key="step.number">
              <div class="flex items-center">
                <div
                  :class="[
                    'w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all',
                    currentStep >= step.number
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-200 text-gray-400'
                  ]"
                >
                  <svg v-if="currentStep > step.number" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  <span v-else>{{ step.number }}</span>
                </div>
                <div class="ml-3 hidden sm:block">
                  <p
                    :class="[
                      'font-medium',
                      currentStep >= step.number ? 'text-gray-900' : 'text-gray-400'
                    ]"
                  >
                    {{ step.title }}
                  </p>
                  <p class="text-xs text-gray-400">{{ step.description }}</p>
                </div>
              </div>
              <div
                v-if="index < steps.length - 1"
                :class="[
                  'w-16 lg:w-24 h-1 rounded-full mx-2',
                  currentStep > step.number ? 'bg-primary-500' : 'bg-gray-200'
                ]"
              ></div>
            </template>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="bg-white rounded-2xl shadow-soft p-6 lg:p-10">
          <!-- ==================== 声音档案流程 ==================== -->
          <template v-if="profileType === 'voice'">
            <!-- Step 1: 上传音频 -->
            <div v-if="currentStep === 1">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Upload Your Voice</h2>
              <p class="text-gray-500 mb-6">Record or upload a 10-15 second audio clip of your voice</p>

              <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-primary-300 transition-colors">
                <input
                  type="file"
                  accept="audio/*"
                  @change="handleAudioUpload"
                  class="hidden"
                  id="audio-upload"
                />
                <label for="audio-upload" class="cursor-pointer">
                  <div class="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-full flex items-center justify-center">
                    <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                    </svg>
                  </div>
                  <p class="text-gray-700 font-medium mb-1">Click to upload audio file</p>
                  <p class="text-sm text-gray-400">WAV, MP3 (max 10MB, 10-15 seconds)</p>
                </label>
              </div>

              <div v-if="audioFile" class="mt-6 p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                    <svg class="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                    </svg>
                  </div>
                  <div class="flex-1">
                    <p class="font-medium text-gray-900">{{ audioFile.name }}</p>
                    <p class="text-sm text-gray-500">{{ (audioFile.size / 1024 / 1024).toFixed(2) }} MB</p>
                  </div>
                </div>
                <audio v-if="audioPreviewUrl" :src="audioPreviewUrl" controls class="w-full mt-4"></audio>
              </div>

              <div class="mt-6 p-4 bg-blue-50 rounded-xl">
                <h4 class="font-medium text-blue-900 mb-2">Tips for best results:</h4>
                <ul class="text-sm text-blue-700 space-y-1">
                  <li>- Record in a quiet environment</li>
                  <li>- Speak clearly at a normal pace</li>
                  <li>- Avoid background music or noise</li>
                  <li>- 10-15 seconds is ideal</li>
                </ul>
              </div>
            </div>

            <!-- Step 2: 选择预设故事 -->
            <div v-if="currentStep === 2">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Select Preview Story</h2>
              <p class="text-gray-500 mb-6">Choose a story to preview your cloned voice</p>

              <div v-if="presetStories.length === 0" class="text-center py-8">
                <div class="w-12 h-12 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <svg class="w-6 h-6 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
                <p class="text-gray-500">Loading stories...</p>
              </div>

              <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  v-for="story in presetStories"
                  :key="story.id"
                  @click="selectedStoryId = story.id"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    selectedStoryId === story.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
                      <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <h3 class="font-semibold text-gray-900">{{ story.title }}</h3>
                      <p class="text-sm text-gray-500 mt-1 line-clamp-2">{{ story.preview_text }}</p>
                    </div>
                    <div v-if="selectedStoryId === story.id" class="w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0">
                      <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 3: 创建和保存 -->
            <div v-if="currentStep === 3">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Create Voice Profile</h2>
              <p class="text-gray-500 mb-6">We're cloning your voice, please wait...</p>

              <!-- 处理中 -->
              <div v-if="voiceCreating" class="text-center py-12">
                <div class="w-24 h-24 mx-auto mb-6 relative">
                  <div class="absolute inset-0 rounded-full border-4 border-gray-200"></div>
                  <div
                    class="absolute inset-0 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"
                  ></div>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <span class="text-xl font-bold text-primary-500">{{ voiceTaskProgress }}%</span>
                  </div>
                </div>
                <p class="text-gray-600">Cloning your voice...</p>
                <p class="text-sm text-gray-400 mt-2">This may take 1-2 minutes</p>
              </div>

              <!-- 完成 -->
              <div v-else-if="voiceTaskStatus === 'completed'" class="space-y-6">
                <div class="p-4 bg-green-50 rounded-xl border border-green-200">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-green-900">Voice cloning completed!</p>
                      <p class="text-sm text-green-600">Listen to the preview below</p>
                    </div>
                  </div>
                </div>

                <div v-if="voicePreviewAudioUrl" class="p-4 bg-gray-50 rounded-xl">
                  <p class="text-sm text-gray-500 mb-3">Preview Audio</p>
                  <audio :src="voicePreviewAudioUrl" controls class="w-full"></audio>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Profile Name</label>
                  <input
                    v-model="voiceProfileName"
                    type="text"
                    class="input"
                    placeholder="e.g., Dad's Voice, Mom's Voice"
                  />
                </div>

                <button
                  @click="saveVoiceProfile"
                  :disabled="voiceSaving || !voiceProfileName.trim()"
                  class="btn-primary w-full py-4 text-lg disabled:opacity-50"
                >
                  {{ voiceSaving ? 'Saving...' : 'Save Voice Profile' }}
                </button>
              </div>

              <!-- 失败 -->
              <div v-else-if="voiceTaskStatus === 'failed'" class="text-center py-12">
                <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                  <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
                <p class="text-gray-600 mb-4">Voice cloning failed</p>
                <button @click="currentStep = 1" class="btn-secondary">Try Again</button>
              </div>
            </div>
          </template>

          <!-- ==================== 数字人档案流程 ==================== -->
          <template v-if="profileType === 'avatar'">
            <!-- Step 1: 上传照片 -->
            <div v-if="currentStep === 1">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Upload Your Photo</h2>
              <p class="text-gray-500 mb-6">Upload a clear photo of your face for best results</p>

              <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-blue-300 transition-colors">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleImageUpload"
                  class="hidden"
                  id="image-upload"
                />
                <label for="image-upload" class="cursor-pointer">
                  <div class="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                  </div>
                  <p class="text-gray-700 font-medium mb-1">Click to upload photo</p>
                  <p class="text-sm text-gray-400">JPG, PNG (max 5MB)</p>
                </label>
              </div>

              <div v-if="imageFile" class="mt-6">
                <div class="relative w-48 h-48 mx-auto rounded-xl overflow-hidden">
                  <img :src="imagePreviewUrl" class="w-full h-full object-cover" />
                </div>
                <p class="text-center text-sm text-gray-500 mt-2">{{ imageFile.name }}</p>
              </div>

              <div class="mt-6 p-4 bg-blue-50 rounded-xl">
                <h4 class="font-medium text-blue-900 mb-2">Photo requirements:</h4>
                <ul class="text-sm text-blue-700 space-y-1">
                  <li>- Clear, front-facing photo</li>
                  <li>- Good lighting, no shadows on face</li>
                  <li>- Neutral expression works best</li>
                  <li>- Face should be clearly visible</li>
                </ul>
              </div>
            </div>

            <!-- Step 2: 选择声音（可选） -->
            <div v-if="currentStep === 2">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Select Voice (Optional)</h2>
              <p class="text-gray-500 mb-6">Choose a voice profile to generate preview video</p>

              <div v-if="voiceProfiles.length === 0" class="text-center py-8 bg-gray-50 rounded-xl">
                <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                  </svg>
                </div>
                <p class="text-gray-500 mb-2">No voice profiles yet</p>
                <p class="text-sm text-gray-400">You can skip this step and use default voice</p>
              </div>

              <div v-else class="space-y-4">
                <!-- 不选择声音 -->
                <div
                  @click="selectedVoiceProfileId = ''"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    !selectedVoiceProfileId
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <p class="font-medium text-gray-900">Skip (Use default voice)</p>
                      <p class="text-sm text-gray-500">Generate avatar without voice preview</p>
                    </div>
                  </div>
                </div>

                <!-- 声音列表 -->
                <div
                  v-for="profile in voiceProfiles"
                  :key="profile.id"
                  @click="selectedVoiceProfileId = profile.id"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    selectedVoiceProfileId === profile.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <p class="font-medium text-gray-900">{{ profile.name }}</p>
                      <p class="text-sm text-gray-500">Created {{ new Date(profile.created_at).toLocaleDateString() }}</p>
                    </div>
                    <div v-if="selectedVoiceProfileId === profile.id" class="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
                      <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 3: 创建和保存 -->
            <div v-if="currentStep === 3">
              <h2 class="text-xl font-bold text-gray-900 mb-2">Create Avatar Profile</h2>
              <p class="text-gray-500 mb-6">We're generating your digital avatar...</p>

              <!-- 处理中 -->
              <div v-if="avatarCreating" class="text-center py-12">
                <div class="w-24 h-24 mx-auto mb-6 relative">
                  <div class="absolute inset-0 rounded-full border-4 border-gray-200"></div>
                  <div
                    class="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"
                  ></div>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <span class="text-xl font-bold text-blue-500">{{ avatarTaskProgress }}%</span>
                  </div>
                </div>
                <p class="text-gray-600">Creating your digital avatar...</p>
                <p class="text-sm text-gray-400 mt-2">This may take 2-3 minutes</p>
              </div>

              <!-- 完成 -->
              <div v-else-if="avatarTaskStatus === 'completed'" class="space-y-6">
                <div class="p-4 bg-green-50 rounded-xl border border-green-200">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-green-900">Avatar created successfully!</p>
                      <p class="text-sm text-green-600">Preview your digital avatar below</p>
                    </div>
                  </div>
                </div>

                <div v-if="avatarPreviewVideoUrl" class="rounded-xl overflow-hidden">
                  <video :src="avatarPreviewVideoUrl" controls autoplay loop class="w-full max-w-md mx-auto"></video>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Profile Name</label>
                  <input
                    v-model="avatarProfileName"
                    type="text"
                    class="input"
                    placeholder="e.g., Dad's Avatar, Mom's Avatar"
                  />
                </div>

                <button
                  @click="saveAvatarProfile"
                  :disabled="avatarSaving || !avatarProfileName.trim()"
                  class="btn-primary w-full py-4 text-lg disabled:opacity-50"
                >
                  {{ avatarSaving ? 'Saving...' : 'Save Avatar Profile' }}
                </button>
              </div>

              <!-- 失败 -->
              <div v-else-if="avatarTaskStatus === 'failed'" class="text-center py-12">
                <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                  <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
                <p class="text-gray-600 mb-4">Avatar creation failed</p>
                <button @click="currentStep = 1" class="btn-secondary">Try Again</button>
              </div>
            </div>
          </template>

          <!-- 导航按钮 -->
          <div v-if="currentStep < 3 || (profileType === 'voice' && voiceTaskStatus !== 'completed') || (profileType === 'avatar' && avatarTaskStatus !== 'completed')" class="flex justify-between mt-8 pt-6 border-t">
            <button
              v-if="currentStep > 1"
              @click="prevStep"
              class="btn-secondary"
              :disabled="(profileType === 'voice' && voiceCreating) || (profileType === 'avatar' && avatarCreating)"
            >
              Previous
            </button>
            <div v-else></div>

            <button
              v-if="currentStep < 3"
              @click="nextStep"
              :disabled="!canProceed"
              class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
