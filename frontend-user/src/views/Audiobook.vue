<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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

// 上传电子书状态
const showUploadModal = ref(false)
const uploading = ref(false)
const newEbook = ref({
  title: '',
  content: '',
  language: 'zh'
})

// 当前选项卡
const activeTab = ref<'templates' | 'myebooks'>('templates')

// 选择来源类型
const sourceType = ref<'story' | 'ebook'>('story')

// 加载数据
onMounted(async () => {
  try {
    const [storiesRes, profilesRes, jobsRes, ebooksRes] = await Promise.all([
      audiobookApi.getStories({ page_size: 20 }),
      voiceCloneApi.getProfiles(),
      audiobookApi.getJobs({ page_size: 10 }),
      audiobookApi.getEbooks({ page_size: 20 })
    ])
    stories.value = storiesRes.data.items
    voiceProfiles.value = profilesRes.data.profiles
    jobs.value = jobsRes.data.items
    ebooks.value = ebooksRes.data.items
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
})

// 从模板创建
const openCreateModal = (story: AudiobookStory) => {
  selectedStory.value = story
  selectedEbook.value = null
  sourceType.value = 'story'
  showModal.value = true
}

// 从电子书创建
const openCreateFromEbook = (ebook: UserEbook) => {
  selectedEbook.value = ebook
  selectedStory.value = null
  sourceType.value = 'ebook'
  showModal.value = true
}

// 创建有声书
const createAudiobook = async () => {
  if (!selectedVoice.value) return

  generating.value = true
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
    alert('Creation failed, please try again')
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

      <!-- My Audiobooks -->
      <div v-if="jobs.length > 0" class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">My Audiobooks</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="job in jobs"
            :key="job.id"
            class="bg-white rounded-xl p-4 shadow-soft"
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
              <audio
                v-if="job.status === 'completed' && job.audio_url"
                :src="job.audio_url"
                controls
                class="w-32"
              ></audio>
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
        <div class="absolute inset-0 bg-black/50" @click="showModal = false"></div>
        <div class="relative bg-white rounded-2xl p-6 max-w-md w-full shadow-xl">
          <h3 class="text-xl font-bold text-gray-900 mb-2">Select Voice</h3>
          <p class="text-sm text-gray-500 mb-4">
            Creating audiobook for: <span class="font-medium text-gray-700">{{ selectedTitle }}</span>
          </p>

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
