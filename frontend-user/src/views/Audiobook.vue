<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { audiobookApi, voiceCloneApi } from '@/api'
import type { AudiobookStory, VoiceProfile, AudiobookJob, UserEbook } from '@/types'

// 数据状态
const stories = ref<AudiobookStory[]>([])
const voiceProfiles = ref<VoiceProfile[]>([])
const jobs = ref<AudiobookJob[]>([])
const ebooks = ref<UserEbook[]>([])
const loading = ref(true)

// 选择状态
const selectedStory = ref<AudiobookStory | null>(null)
const selectedEbook = ref<UserEbook | null>(null)
const selectedVoice = ref<VoiceProfile | null>(null)
const showModal = ref(false)
const generating = ref(false)
const creationError = ref('')

// 上传电子书状态
const showUploadModal = ref(false)
const uploading = ref(false)
const newEbook = ref({
  title: '',
  content: '',
  language: 'zh'
})

// Job 下拉菜单状态
const openJobMenuId = ref<string | null>(null)

// 计算收藏和非收藏的任务
const favoriteJobs = computed(() => jobs.value.filter(job => job.is_favorite))
const regularJobs = computed(() => jobs.value.filter(job => !job.is_favorite))

// 当前选项卡
const activeTab = ref<'templates' | 'myebooks'>('templates')

// 选择来源类型
const sourceType = ref<'story' | 'ebook'>('story')

// 点击外部关闭菜单
const handleClickOutside = (e: MouseEvent) => {
  if (openJobMenuId.value) {
    openJobMenuId.value = null
  }
}

// 加载数据 - 每个 API 独立处理错误
onMounted(async () => {
  // 注册点击外部关闭菜单事件
  document.addEventListener('click', handleClickOutside)
  try {
    // 加载故事模板
    audiobookApi.getStories({ page_size: 20 })
      .then(res => { stories.value = res.data.items })
      .catch(e => console.error('Failed to load stories:', e))

    // 加载声音档案
    voiceCloneApi.getProfiles()
      .then(res => { voiceProfiles.value = res.data.profiles })
      .catch(e => console.error('Failed to load voice profiles:', e))

    // 加载有声书任务
    audiobookApi.getJobs({ page_size: 10 })
      .then(res => { jobs.value = res.data.items })
      .catch(e => console.error('Failed to load jobs:', e))

    // 加载用户电子书
    audiobookApi.getEbooks({ page_size: 20 })
      .then(res => { ebooks.value = res.data.items })
      .catch(e => console.error('Failed to load ebooks:', e))
  } finally {
    // 给一点时间让请求完成
    setTimeout(() => {
      loading.value = false
    }, 500)
  }
})

// 清理事件监听
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 刷新声音档案
const refreshVoiceProfiles = async () => {
  try {
    const res = await voiceCloneApi.getProfiles()
    voiceProfiles.value = res.data.profiles
  } catch (e) {
    console.error('Failed to refresh voice profiles:', e)
  }
}

// 从模板创建
const openCreateModal = async (story: AudiobookStory) => {
  selectedStory.value = story
  selectedEbook.value = null
  sourceType.value = 'story'
  showModal.value = true
  // 打开模态框时刷新声音档案
  await refreshVoiceProfiles()
}

// 从电子书创建
const openCreateFromEbook = async (ebook: UserEbook) => {
  selectedEbook.value = ebook
  selectedStory.value = null
  sourceType.value = 'ebook'
  showModal.value = true
  // 打开模态框时刷新声音档案
  await refreshVoiceProfiles()
}

// 创建有声书
const createAudiobook = async () => {
  if (!selectedVoice.value) return

  generating.value = true
  creationError.value = ''
  try {
    if (sourceType.value === 'story' && selectedStory.value) {
      const res = await audiobookApi.createJob(selectedStory.value.id, selectedVoice.value.id)
      jobs.value.unshift(res.data)
    } else if (sourceType.value === 'ebook' && selectedEbook.value) {
      const res = await audiobookApi.createJobFromEbook(selectedEbook.value.id, selectedVoice.value.id)
      // 刷新任务列表
      const jobsRes = await audiobookApi.getJobs({ page_size: 10 })
      jobs.value = jobsRes.data.items
    }
    showModal.value = false
    selectedStory.value = null
    selectedEbook.value = null
    selectedVoice.value = null
  } catch (e) {
    creationError.value = 'Our service is currently busy. Please try again later.'
  } finally {
    generating.value = false
  }
}

// 上传电子书
const uploadEbook = async () => {
  if (!newEbook.value.title.trim() || !newEbook.value.content.trim()) {
    alert('Please fill in title and content')
    return
  }

  uploading.value = true
  try {
    const res = await audiobookApi.createEbook({
      title: newEbook.value.title.trim(),
      content: newEbook.value.content.trim(),
      language: newEbook.value.language
    })
    ebooks.value.unshift(res.data)
    showUploadModal.value = false
    newEbook.value = { title: '', content: '', language: 'zh' }
    // 切换到我的电子书标签
    activeTab.value = 'myebooks'
  } catch (e) {
    alert('Upload failed, please try again')
  } finally {
    uploading.value = false
  }
}

// 删除电子书
const deleteEbook = async (ebook: UserEbook) => {
  if (!confirm(`Delete "${ebook.title}"?`)) return

  try {
    await audiobookApi.deleteEbook(ebook.id)
    ebooks.value = ebooks.value.filter(e => e.id !== ebook.id)
  } catch (e) {
    alert('Delete failed')
  }
}

// 删除有声书任务
const deleteJob = async (job: AudiobookJob) => {
  if (!confirm(`Delete "${job.story_title}"?`)) return

  try {
    await audiobookApi.deleteJob(job.id)
    jobs.value = jobs.value.filter(j => j.id !== job.id)
    openJobMenuId.value = null
  } catch (e) {
    alert('Delete failed')
  }
}

// 切换收藏状态
const toggleFavorite = async (job: AudiobookJob) => {
  try {
    const res = await audiobookApi.toggleFavorite(job.id)
    // 更新本地状态
    const index = jobs.value.findIndex(j => j.id === job.id)
    if (index !== -1) {
      jobs.value[index].is_favorite = res.data.is_favorite
    }
    openJobMenuId.value = null
  } catch (e) {
    alert('Operation failed')
  }
}

// 切换 Job 菜单
const toggleJobMenu = (jobId: string) => {
  openJobMenuId.value = openJobMenuId.value === jobId ? null : jobId
}

// 格式化时长
const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 选择的来源标题
const selectedTitle = computed(() => {
  if (sourceType.value === 'story' && selectedStory.value) {
    return selectedStory.value.title
  }
  if (sourceType.value === 'ebook' && selectedEbook.value) {
    return selectedEbook.value.title
  }
  return ''
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Audiobook</h1>
          <p class="mt-2 text-gray-600">Generate audiobooks with your voice</p>
        </div>
        <button
          @click="showUploadModal = true"
          class="btn-primary flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Upload Ebook
        </button>
      </div>

      <!-- Favorites Section -->
      <div v-if="favoriteJobs.length > 0" class="mb-8">
        <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
          Favorites
        </h2>
        <div class="max-h-[140px] overflow-y-auto pr-2">
          <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="job in favoriteJobs"
              :key="job.id"
              class="bg-white rounded-xl p-4 shadow-soft relative border-2 border-yellow-100"
            >
              <div class="flex items-center gap-4">
                <div class="w-16 h-16 rounded-lg bg-yellow-50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-8 h-8 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium text-gray-900 truncate">{{ job.story_title }}</h3>
                  <p class="text-sm text-gray-500">{{ job.voice_name }}</p>
                  <div class="mt-1">
                    <span
                      :class="[
                        'text-xs px-2 py-0.5 rounded-full',
                        job.status === 'completed' ? 'bg-green-100 text-green-700' :
                        job.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                        job.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      ]"
                    >
                      {{ job.status === 'completed' ? 'Completed' :
                         job.status === 'processing' ? 'Processing' :
                         job.status === 'failed' ? 'Failed' : 'Pending' }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <audio
                    v-if="job.status === 'completed' && job.audio_url"
                    :src="job.audio_url"
                    controls
                    class="w-28 h-8"
                  ></audio>
                  <div class="relative">
                    <button
                      @click.stop="toggleJobMenu(job.id)"
                      class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="6" r="1.5"/>
                        <circle cx="12" cy="12" r="1.5"/>
                        <circle cx="12" cy="18" r="1.5"/>
                      </svg>
                    </button>
                    <div
                      v-if="openJobMenuId === job.id"
                      class="absolute right-0 top-full mt-1 w-36 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-10"
                    >
                      <button
                        @click="toggleFavorite(job)"
                        class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                        </svg>
                        Unfavorite
                      </button>
                      <button
                        @click="deleteJob(job)"
                        class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- My Audiobooks -->
      <div v-if="regularJobs.length > 0" class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">My Audiobooks</h2>
        <!-- 限制最多显示2行，超出滚动 -->
        <div class="max-h-[280px] overflow-y-auto pr-2">
          <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="job in regularJobs"
              :key="job.id"
              class="bg-white rounded-xl p-4 shadow-soft relative"
            >
              <div class="flex items-center gap-4">
                <div class="w-16 h-16 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium text-gray-900 truncate">{{ job.story_title }}</h3>
                  <p class="text-sm text-gray-500">{{ job.voice_name }}</p>
                  <div class="mt-1">
                    <span
                      :class="[
                        'text-xs px-2 py-0.5 rounded-full',
                        job.status === 'completed' ? 'bg-green-100 text-green-700' :
                        job.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                        job.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      ]"
                    >
                      {{ job.status === 'completed' ? 'Completed' :
                         job.status === 'processing' ? 'Processing' :
                         job.status === 'failed' ? 'Failed' : 'Pending' }}
                    </span>
                  </div>
                </div>
                <!-- 播放器或菜单按钮 -->
                <div class="flex items-center gap-2 flex-shrink-0">
                  <audio
                    v-if="job.status === 'completed' && job.audio_url"
                    :src="job.audio_url"
                    controls
                    class="w-28 h-8"
                  ></audio>
                  <!-- 三点菜单按钮 -->
                  <div class="relative">
                    <button
                      @click.stop="toggleJobMenu(job.id)"
                      class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="6" r="1.5"/>
                        <circle cx="12" cy="12" r="1.5"/>
                        <circle cx="12" cy="18" r="1.5"/>
                      </svg>
                    </button>
                    <!-- 下拉菜单 -->
                    <div
                      v-if="openJobMenuId === job.id"
                      class="absolute right-0 top-full mt-1 w-36 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-10"
                    >
                      <button
                        @click="toggleFavorite(job)"
                        class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                        </svg>
                        Add to Favorites
                      </button>
                      <button
                        @click="deleteJob(job)"
                        class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex gap-8">
            <button
              @click="activeTab = 'templates'"
              :class="[
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'templates'
                  ? 'border-primary-500 text-primary-500'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              Story Templates
            </button>
            <button
              @click="activeTab = 'myebooks'"
              :class="[
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'myebooks'
                  ? 'border-primary-500 text-primary-500'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              My Ebooks
              <span v-if="ebooks.length > 0" class="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                {{ ebooks.length }}
              </span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Story Templates Tab -->
      <div v-if="activeTab === 'templates'">
        <div v-if="loading" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="i in 6" :key="i" class="animate-pulse bg-white rounded-xl p-4">
            <div class="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div class="h-20 bg-gray-200 rounded mb-3"></div>
            <div class="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        </div>

        <div v-else-if="stories.length === 0" class="text-center py-12 text-gray-500">
          No story templates available
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="story in stories"
            :key="story.id"
            class="bg-white rounded-xl p-6 shadow-soft hover:shadow-card transition-shadow"
          >
            <h3 class="font-bold text-gray-900 mb-2">{{ story.title }}</h3>
            <p class="text-gray-600 text-sm line-clamp-3 mb-4">
              {{ story.content.substring(0, 150) }}...
            </p>
            <div class="flex items-center justify-between">
              <div class="flex gap-2">
                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {{ story.language === 'zh' ? 'Chinese' : 'English' }}
                </span>
                <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  {{ story.category }}
                </span>
              </div>
              <button
                @click="openCreateModal(story)"
                class="btn-primary text-sm py-2 px-4"
              >
                Create Audiobook
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- My Ebooks Tab -->
      <div v-if="activeTab === 'myebooks'">
        <div v-if="ebooks.length === 0" class="text-center py-12">
          <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <p class="text-gray-500 mb-4">You haven't uploaded any ebooks yet</p>
          <button
            @click="showUploadModal = true"
            class="btn-primary"
          >
            Upload Your First Ebook
          </button>
        </div>

        <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="ebook in ebooks"
            :key="ebook.id"
            class="bg-white rounded-xl p-6 shadow-soft hover:shadow-card transition-shadow"
          >
            <div class="flex items-start justify-between mb-3">
              <h3 class="font-bold text-gray-900">{{ ebook.title }}</h3>
              <button
                @click="deleteEbook(ebook)"
                class="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Delete"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            <p class="text-gray-600 text-sm line-clamp-3 mb-4">
              {{ ebook.content.substring(0, 150) }}...
            </p>
            <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
              <span>{{ ebook.metadata.char_count }} chars</span>
              <span>~{{ formatDuration(ebook.metadata.estimated_duration) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                {{ ebook.language === 'zh' ? 'Chinese' : 'English' }}
              </span>
              <button
                @click="openCreateFromEbook(ebook)"
                class="btn-primary text-sm py-2 px-4"
              >
                Create Audiobook
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Audiobook Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div class="absolute inset-0 bg-black/50" @click="showModal = false; creationError = ''"></div>
        <div class="relative bg-white rounded-2xl p-6 max-w-md w-full shadow-xl">
          <h3 class="text-xl font-bold text-gray-900 mb-2">Select Voice</h3>
          <p class="text-sm text-gray-500 mb-4">
            Creating audiobook for: <span class="font-medium text-gray-700">{{ selectedTitle }}</span>
          </p>

          <!-- Error Message -->
          <div v-if="creationError" class="mb-4 p-4 bg-gradient-to-r from-orange-50 to-orange-100/50 border border-orange-200 rounded-xl">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">Service Temporarily Unavailable</p>
                <p class="text-sm text-gray-600 mt-0.5">{{ creationError }}</p>
              </div>
            </div>
          </div>

          <div v-if="voiceProfiles.length === 0" class="text-center py-8 text-gray-500">
            <p>You don't have any voice profiles yet</p>
            <RouterLink to="/profiles/voice" class="text-primary-500 hover:underline">
              Create a voice profile
            </RouterLink>
          </div>

          <div v-else class="space-y-3 max-h-64 overflow-y-auto">
            <div
              v-for="profile in voiceProfiles"
              :key="profile.id"
              @click="selectedVoice = profile"
              :class="[
                'p-4 rounded-xl border-2 cursor-pointer transition-all',
                selectedVoice?.id === profile.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <p class="font-medium text-gray-900">{{ profile.name }}</p>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="showModal = false"
              class="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="createAudiobook"
              :disabled="!selectedVoice || generating"
              class="flex-1 btn-primary disabled:opacity-50"
            >
              {{ generating ? 'Creating...' : 'Start Generation' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Upload Ebook Modal -->
    <Teleport to="body">
      <div
        v-if="showUploadModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div class="absolute inset-0 bg-black/50" @click="showUploadModal = false"></div>
        <div class="relative bg-white rounded-2xl p-6 max-w-lg w-full shadow-xl">
          <h3 class="text-xl font-bold text-gray-900 mb-4">Upload Ebook</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                v-model="newEbook.title"
                type="text"
                placeholder="Enter ebook title"
                class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select
                v-model="newEbook.language"
                class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="zh">Chinese</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Content</label>
              <textarea
                v-model="newEbook.content"
                rows="10"
                placeholder="Paste your story text here..."
                class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              ></textarea>
              <p class="mt-1 text-xs text-gray-500">
                {{ newEbook.content.length }} characters
              </p>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="showUploadModal = false"
              class="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="uploadEbook"
              :disabled="uploading || !newEbook.title.trim() || !newEbook.content.trim()"
              class="flex-1 btn-primary disabled:opacity-50"
            >
              {{ uploading ? 'Uploading...' : 'Upload' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
