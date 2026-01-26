<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { storyApi, voiceCloneApi, digitalHumanApi, storyGenerationApi } from '@/api'
import type { Story, VoiceProfile, AvatarProfile, Speaker, SpeakerConfig, GenerationMode, SingleSpeakerAnalysis, DualSpeakerAnalysis } from '@/types'

const route = useRoute()

const currentStep = ref(1)

const stories = ref<Story[]>([])
const selectedStory = ref<Story | null>(null)
const storiesLoading = ref(false)

// 生成模式选择：single=单人模式, dual=双人模式
const generationMode = ref<GenerationMode>('single')

// 单人模式分析结果
const singleSpeakerAnalysis = ref<SingleSpeakerAnalysis | null>(null)

// 双人模式分析结果
const dualSpeakerAnalysis = ref<DualSpeakerAnalysis | null>(null)

// 说话人相关状态 (用于双人模式)
const speakers = ref<Speaker[]>([])
const speakersLoading = ref(false)
const isAnalyzed = ref(false)
const analysisError = ref('')
// 每个说话人的配置：{ speaker_id: { voice_profile_id, avatar_profile_id } }
const speakerConfigs = ref<Record<string, { voice_profile_id: string | null; avatar_profile_id: string | null }>>({})

// 单人模式配置
const singleModeVoiceProfileId = ref<string | null>(null)
const singleModeAvatarProfileId = ref<string | null>(null)

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
const generationError = ref('')

// 检查单人模式是否可用
const isSingleModeAvailable = computed(() => {
  return singleSpeakerAnalysis.value?.is_analyzed === true
})

// 检查双人模式是否可用
const isDualModeAvailable = computed(() => {
  return dualSpeakerAnalysis.value?.is_analyzed === true && (dualSpeakerAnalysis.value?.speakers?.length ?? 0) > 1
})

// 是否有任何模式可用
const isAnyModeAvailable = computed(() => {
  return isSingleModeAvailable.value || isDualModeAvailable.value
})

const steps = [
  { number: '1', title: 'Choose Story', icon: '/icons/icon-storybook.png' },
  { number: '2', title: 'Configure Voices', icon: '/icons/icon-microphone.png' },
  { number: '3', title: 'Configure Avatars', icon: '/icons/icon-avatar.png' },
  { number: '4', title: 'Generate', icon: '/icons/icon-sparkles.png' }
]

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      // 需要选择故事且至少有一种模式可用
      return !!selectedStory.value && isAnyModeAvailable.value
    case 2:
      // 根据模式检查声音配置
      if (generationMode.value === 'single') {
        return !!singleModeVoiceProfileId.value
      } else {
        // 双人模式：每个说话人都需要配置声音
        return speakers.value.every(s => speakerConfigs.value[s.speaker_id]?.voice_profile_id)
      }
    case 3:
      // 根据模式检查头像配置
      if (generationMode.value === 'single') {
        return !!singleModeAvatarProfileId.value
      } else {
        // 双人模式：每个说话人都需要配置头像
        return speakers.value.every(s => speakerConfigs.value[s.speaker_id]?.avatar_profile_id)
      }
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

// 加载说话人信息和分析结果
const loadSpeakers = async (storyId: string) => {
  speakersLoading.value = true
  speakers.value = []
  isAnalyzed.value = false
  analysisError.value = ''
  speakerConfigs.value = {}
  singleSpeakerAnalysis.value = null
  dualSpeakerAnalysis.value = null

  try {
    const res = await storyGenerationApi.getSpeakers(storyId)

    // 保存分析结果
    singleSpeakerAnalysis.value = res.data.single_speaker_analysis || null
    dualSpeakerAnalysis.value = res.data.dual_speaker_analysis || null

    // 从双人模式分析结果获取说话人列表
    if (dualSpeakerAnalysis.value?.speakers) {
      speakers.value = dualSpeakerAnalysis.value.speakers
    } else {
      speakers.value = res.data.speakers || []
    }

    isAnalyzed.value = res.data.is_analyzed
    analysisError.value = res.data.analysis_error || ''

    // 初始化每个说话人的配置
    for (const speaker of speakers.value) {
      speakerConfigs.value[speaker.speaker_id] = {
        voice_profile_id: null,
        avatar_profile_id: null
      }
    }

    // 自动选择可用的模式
    if (singleSpeakerAnalysis.value?.is_analyzed) {
      generationMode.value = 'single'
    } else if (dualSpeakerAnalysis.value?.is_analyzed) {
      generationMode.value = 'dual'
    }

  } catch (e) {
    console.error('Failed to load speakers:', e)
  } finally {
    speakersLoading.value = false
  }
}

// 监听故事选择变化，自动加载说话人信息
watch(selectedStory, async (newStory) => {
  if (newStory) {
    await loadSpeakers(newStory.id)
  }
})

// 设置说话人的声音档案
const setSpeakerVoice = (speakerId: string, voiceProfileId: string | null) => {
  if (speakerConfigs.value[speakerId]) {
    speakerConfigs.value[speakerId].voice_profile_id = voiceProfileId
  }
}

// 设置说话人的头像档案
const setSpeakerAvatar = (speakerId: string, avatarProfileId: string | null) => {
  if (speakerConfigs.value[speakerId]) {
    speakerConfigs.value[speakerId].avatar_profile_id = avatarProfileId
  }
}

// 获取说话人标签显示名称
const getSpeakerLabel = (speaker: Speaker) => {
  if (speaker.label) return speaker.label
  if (speaker.gender === 'male') return 'Male Voice'
  if (speaker.gender === 'female') return 'Female Voice'
  return speaker.speaker_id
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
  if (!selectedStory.value) return

  // 根据模式检查配置
  if (generationMode.value === 'single') {
    if (!singleModeVoiceProfileId.value || !singleModeAvatarProfileId.value) return
  } else {
    // 双人模式：检查所有说话人都配置了声音和头像
    const allConfigured = speakers.value.every(s =>
      speakerConfigs.value[s.speaker_id]?.voice_profile_id &&
      speakerConfigs.value[s.speaker_id]?.avatar_profile_id
    )
    if (!allConfigured) return
  }

  generating.value = true
  progress.value = 0
  currentTask.value = 'Preparing...'
  generationError.value = ''

  try {
    let requestData: any = {
      story_id: selectedStory.value.id,
      mode: generationMode.value,
      full_video: false
    }

    if (generationMode.value === 'single') {
      // 单人模式：使用单一声音和头像
      requestData.voice_profile_id = singleModeVoiceProfileId.value
      requestData.avatar_profile_id = singleModeAvatarProfileId.value
    } else {
      // 双人模式：构建 speaker_configs 数组
      const configs: SpeakerConfig[] = speakers.value.map(speaker => ({
        speaker_id: speaker.speaker_id,
        voice_profile_id: speakerConfigs.value[speaker.speaker_id]?.voice_profile_id || null,
        avatar_profile_id: speakerConfigs.value[speaker.speaker_id]?.avatar_profile_id || null,
        enabled: true
      }))
      requestData.speaker_configs = configs
    }

    const res = await storyGenerationApi.createJob(requestData)

    const jobId = res.data.id
    const pollStatus = async () => {
      const statusRes = await storyGenerationApi.getJob(jobId)
      const job = statusRes.data
      progress.value = job.progress
      currentTask.value = job.current_step

      if (job.status === 'completed') {
        resultVideoUrl.value = job.final_video_url || ''
        generating.value = false
      } else if (job.status === 'failed') {
        generationError.value = 'Our service is currently busy. Please try again later.'
        generating.value = false
      } else {
        setTimeout(pollStatus, 2000)
      }
    }
    pollStatus()
  } catch (e) {
    console.error('Failed to start generation:', e)
    generating.value = false
    generationError.value = 'Our service is currently busy. Please try again later.'
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

          <!-- 显示选中故事的说话人信息 -->
          <div v-if="selectedStory" class="mt-6 p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center gap-4">
              <img
                :src="selectedStory.thumbnail_url"
                class="w-20 h-14 rounded-lg object-cover"
              />
              <div class="flex-1">
                <h3 class="font-semibold text-gray-900">{{ selectedStory.title_en || selectedStory.title }}</h3>
                <div class="flex items-center gap-2 mt-1">
                  <span v-if="speakersLoading" class="text-sm text-gray-500">Analyzing story audio...</span>
                  <span v-else-if="!isAnyModeAvailable && !analysisError" class="text-sm text-yellow-600">
                    Story not analyzed yet
                  </span>
                  <span v-else-if="analysisError" class="text-sm text-red-500">
                    Analysis error: {{ analysisError }}
                  </span>
                  <template v-else>
                    <span v-if="isSingleModeAvailable" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      Single Mode Ready
                    </span>
                    <span v-if="isDualModeAvailable" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      Dual Mode Ready ({{ speakers.length }} speakers)
                    </span>
                  </template>
                </div>
              </div>
            </div>

            <!-- 模式选择 -->
            <div v-if="isAnyModeAvailable && !speakersLoading" class="mt-4 pt-4 border-t border-gray-200">
              <h4 class="font-medium text-gray-900 mb-3">Select Generation Mode</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <!-- 单人模式 -->
                <div
                  v-if="isSingleModeAvailable"
                  @click="generationMode = 'single'"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    generationMode === 'single'
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <h5 class="font-semibold text-gray-900">Single Person Mode</h5>
                      <p class="text-sm text-gray-500">One voice and avatar for the entire story</p>
                    </div>
                    <div v-if="generationMode === 'single'" class="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center">
                      <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- 双人模式 -->
                <div
                  v-if="isDualModeAvailable"
                  @click="generationMode = 'dual'"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    generationMode === 'dual'
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                      <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <h5 class="font-semibold text-gray-900">Dual Person Mode</h5>
                      <p class="text-sm text-gray-500">Different voice and avatar for each speaker</p>
                    </div>
                    <div v-if="generationMode === 'dual'" class="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center">
                      <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 双人模式：显示说话人信息 -->
              <div v-if="generationMode === 'dual' && speakers.length > 0" class="mt-3 p-3 bg-blue-50 rounded-lg">
                <p class="text-sm text-blue-700 font-medium mb-2">Detected Speakers:</p>
                <div class="flex flex-wrap gap-2">
                  <span v-for="speaker in speakers" :key="speaker.speaker_id"
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="speaker.gender === 'male' ? 'bg-blue-100 text-blue-700' : speaker.gender === 'female' ? 'bg-pink-100 text-pink-700' : 'bg-gray-100 text-gray-700'"
                  >
                    {{ getSpeakerLabel(speaker) }} ({{ Math.round(speaker.duration) }}s)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Voice -->
        <div v-else-if="currentStep === 2">
          <h2 class="text-xl font-bold text-gray-900 mb-6">
            {{ generationMode === 'dual' ? 'Configure Voice for Each Speaker' : 'Select Voice Profile' }}
          </h2>

          <!-- 单人模式：选择单一声音 -->
          <template v-if="generationMode === 'single'">
            <div class="p-4 bg-green-50 rounded-xl border border-green-100 mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900">Single Person Mode</h3>
                  <p class="text-sm text-gray-500">Select one voice for the entire story narration</p>
                </div>
              </div>
            </div>

            <div v-if="voiceProfiles.length > 0" class="mb-8">
              <h3 class="text-sm font-medium text-gray-500 mb-3">My Voice Profiles</h3>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div
                  v-for="profile in voiceProfiles"
                  :key="profile.id"
                  @click="singleModeVoiceProfileId = profile.id"
                  :class="[
                    'p-4 rounded-xl border-2 cursor-pointer transition-all',
                    singleModeVoiceProfileId === profile.id
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
                    <div v-if="singleModeVoiceProfileId === profile.id" class="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center">
                      <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-8">
              <p class="text-gray-500">No voice profiles available. Please create one first.</p>
            </div>
          </template>

          <!-- 双人模式：为每个说话人配置声音 -->
          <template v-else>
            <div class="p-4 bg-blue-50 rounded-xl border border-blue-100 mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900">Dual Person Mode</h3>
                  <p class="text-sm text-gray-500">Configure different voices for each speaker</p>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div v-for="speaker in speakers" :key="speaker.speaker_id" class="p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-3 mb-4">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center"
                    :class="speaker.gender === 'male' ? 'bg-blue-100' : speaker.gender === 'female' ? 'bg-pink-100' : 'bg-gray-200'"
                  >
                    <svg class="w-5 h-5" :class="speaker.gender === 'male' ? 'text-blue-600' : speaker.gender === 'female' ? 'text-pink-600' : 'text-gray-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900">{{ getSpeakerLabel(speaker) }}</h3>
                    <p class="text-sm text-gray-500">Duration: {{ Math.round(speaker.duration) }}s</p>
                  </div>
                  <div v-if="speaker.audio_url" class="ml-auto">
                    <audio :src="speaker.audio_url" controls class="h-8"></audio>
                  </div>
                </div>

                <!-- 声音档案选择 -->
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div
                    v-for="profile in voiceProfiles"
                    :key="profile.id"
                    @click="setSpeakerVoice(speaker.speaker_id, profile.id)"
                    :class="[
                      'p-3 rounded-lg border-2 cursor-pointer transition-all',
                      speakerConfigs[speaker.speaker_id]?.voice_profile_id === profile.id
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    ]"
                  >
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                        <img src="/icons/icon-microphone.png" alt="" class="w-4 h-4 object-contain" />
                      </div>
                      <p class="font-medium text-gray-900 text-sm truncate">{{ profile.name }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Step 3: Avatar -->
        <div v-else-if="currentStep === 3">
          <h2 class="text-xl font-bold text-gray-900 mb-6">
            {{ generationMode === 'dual' ? 'Configure Avatar for Each Speaker' : 'Select Avatar Profile' }}
          </h2>

          <!-- 单人模式：选择单一头像 -->
          <template v-if="generationMode === 'single'">
            <div class="p-4 bg-green-50 rounded-xl border border-green-100 mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900">Single Person Mode</h3>
                  <p class="text-sm text-gray-500">Select one avatar for the digital human</p>
                </div>
              </div>
            </div>

            <div v-if="avatarProfiles.length > 0" class="mb-8">
              <h3 class="text-sm font-medium text-gray-500 mb-3">My Avatar Profiles</h3>
              <div class="grid grid-cols-3 md:grid-cols-4 gap-4">
                <div
                  v-for="profile in avatarProfiles"
                  :key="profile.id"
                  @click="singleModeAvatarProfileId = profile.id"
                  :class="[
                    'relative rounded-xl overflow-hidden cursor-pointer transition-all border-2',
                    singleModeAvatarProfileId === profile.id
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
                  <div v-if="singleModeAvatarProfileId === profile.id" class="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-8">
              <p class="text-gray-500">No avatar profiles available. Please create one first.</p>
            </div>
          </template>

          <!-- 双人模式：为每个说话人配置头像 -->
          <template v-else>
            <div class="p-4 bg-blue-50 rounded-xl border border-blue-100 mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900">Dual Person Mode</h3>
                  <p class="text-sm text-gray-500">Configure different avatars for each speaker (dual digital human layout)</p>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div v-for="speaker in speakers" :key="speaker.speaker_id" class="p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-3 mb-4">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center"
                    :class="speaker.gender === 'male' ? 'bg-blue-100' : speaker.gender === 'female' ? 'bg-pink-100' : 'bg-gray-200'"
                  >
                    <svg class="w-5 h-5" :class="speaker.gender === 'male' ? 'text-blue-600' : speaker.gender === 'female' ? 'text-pink-600' : 'text-gray-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900">{{ getSpeakerLabel(speaker) }}</h3>
                    <p class="text-sm text-gray-500">
                      Voice: {{ voiceProfiles.find(v => v.id === speakerConfigs[speaker.speaker_id]?.voice_profile_id)?.name || 'Not selected' }}
                    </p>
                  </div>
                </div>

                <!-- 头像档案选择 -->
                <div class="grid grid-cols-3 md:grid-cols-4 gap-3">
                  <div
                    v-for="profile in avatarProfiles"
                    :key="profile.id"
                    @click="setSpeakerAvatar(speaker.speaker_id, profile.id)"
                    :class="[
                      'relative rounded-xl overflow-hidden cursor-pointer transition-all border-2',
                      speakerConfigs[speaker.speaker_id]?.avatar_profile_id === profile.id
                        ? 'border-primary-500 ring-2 ring-primary-100'
                        : 'border-transparent hover:border-gray-200'
                    ]"
                  >
                    <img
                      :src="profile.image_url"
                      :alt="profile.name"
                      class="w-full aspect-square object-cover"
                    />
                    <div class="absolute bottom-0 left-0 right-0 p-1 bg-black/50">
                      <p class="text-white text-xs text-center truncate">{{ profile.name }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Step 4: Generate -->
        <div v-else-if="currentStep === 4">
          <div v-if="!generating && !resultVideoUrl && !generationError">
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

              <!-- 单人模式：显示选择的声音和头像 -->
              <template v-if="generationMode === 'single'">
                <div class="p-4 bg-green-50 rounded-xl border border-green-100 mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    <span class="font-medium text-green-700">Single Person Mode</span>
                  </div>
                  <p class="text-sm text-gray-600">One voice and avatar will be used for the entire story</p>
                </div>

                <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                  <div class="w-16 h-16 rounded-lg bg-primary-100 flex items-center justify-center">
                    <img src="/icons/icon-microphone.png" alt="" class="w-8 h-8 object-contain" />
                  </div>
                  <div>
                    <p class="text-sm text-gray-500">Voice</p>
                    <p class="font-medium text-gray-900">{{ voiceProfiles.find(v => v.id === singleModeVoiceProfileId)?.name || 'Not selected' }}</p>
                  </div>
                </div>

                <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                  <img
                    v-if="singleModeAvatarProfileId"
                    :src="avatarProfiles.find(a => a.id === singleModeAvatarProfileId)?.image_url"
                    class="w-16 h-16 rounded-lg object-cover"
                  />
                  <div v-else class="w-16 h-16 rounded-lg bg-gray-200 flex items-center justify-center">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm text-gray-500">Avatar</p>
                    <p class="font-medium text-gray-900">{{ avatarProfiles.find(a => a.id === singleModeAvatarProfileId)?.name || 'Not selected' }}</p>
                  </div>
                </div>
              </template>

              <!-- 双人模式：显示每个说话人的配置 -->
              <template v-else>
                <div class="p-4 bg-blue-50 rounded-xl border border-blue-100 mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                    </svg>
                    <span class="font-medium text-blue-700">Dual Person Mode</span>
                  </div>
                  <p class="text-sm text-gray-600">Different voices and avatars for each speaker (dual digital human layout)</p>
                </div>

                <div v-for="speaker in speakers" :key="speaker.speaker_id" class="p-4 bg-gray-50 rounded-xl">
                  <div class="flex items-center gap-4">
                    <div class="w-16 h-16 rounded-lg flex items-center justify-center"
                      :class="speaker.gender === 'male' ? 'bg-blue-100' : speaker.gender === 'female' ? 'bg-pink-100' : 'bg-gray-200'"
                    >
                      <svg class="w-8 h-8" :class="speaker.gender === 'male' ? 'text-blue-600' : speaker.gender === 'female' ? 'text-pink-600' : 'text-gray-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <p class="font-medium text-gray-900">{{ getSpeakerLabel(speaker) }}</p>
                      <div class="flex flex-wrap gap-2 mt-1">
                        <span class="text-sm text-gray-500">
                          Voice: {{ speakerConfigs[speaker.speaker_id]?.voice_profile_id
                            ? voiceProfiles.find(v => v.id === speakerConfigs[speaker.speaker_id]?.voice_profile_id)?.name
                            : 'Not selected' }}
                        </span>
                        <span class="text-sm text-gray-500">|</span>
                        <span class="text-sm text-gray-500">
                          Avatar: {{ speakerConfigs[speaker.speaker_id]?.avatar_profile_id
                            ? avatarProfiles.find(a => a.id === speakerConfigs[speaker.speaker_id]?.avatar_profile_id)?.name
                            : 'Not selected' }}
                        </span>
                      </div>
                    </div>
                    <img
                      v-if="speakerConfigs[speaker.speaker_id]?.avatar_profile_id"
                      :src="avatarProfiles.find(a => a.id === speakerConfigs[speaker.speaker_id]?.avatar_profile_id)?.image_url"
                      class="w-12 h-12 rounded-lg object-cover"
                    />
                  </div>
                </div>
              </template>
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

          <!-- Error State -->
          <div v-else-if="generationError" class="text-center py-12">
            <div class="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-orange-100 to-orange-50 rounded-full flex items-center justify-center">
              <svg class="w-10 h-10 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-3">Service Temporarily Unavailable</h3>
            <p class="text-gray-500 mb-8 max-w-md mx-auto">{{ generationError }}</p>
            <div class="flex gap-4 justify-center">
              <button
                @click="generationError = ''; startGeneration()"
                class="btn-primary"
              >
                Try Again
              </button>
              <button
                @click="generationError = ''; currentStep = 1"
                class="btn-secondary"
              >
                Start Over
              </button>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div v-if="currentStep < 4 || (!generating && !resultVideoUrl && !generationError)" class="flex justify-between mt-8 pt-6 border-t">
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
