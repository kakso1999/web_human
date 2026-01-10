<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { voiceCloneApi } from '@/api'
import type { VoiceProfile } from '@/types'

const profiles = ref<VoiceProfile[]>([])
const loading = ref(true)

// 编辑相关状态
const editingProfile = ref<VoiceProfile | null>(null)
const editName = ref('')
const saving = ref(false)

onMounted(async () => {
  try {
    const res = await voiceCloneApi.getProfiles()
    profiles.value = res.data.profiles
  } finally {
    loading.value = false
  }
})

const deleteProfile = async (id: string) => {
  if (!confirm('Are you sure you want to delete this voice profile?')) return
  try {
    await voiceCloneApi.deleteProfile(id)
    profiles.value = profiles.value.filter(p => p.id !== id)
  } catch (e) {
    alert('Failed to delete')
  }
}

const startEdit = (profile: VoiceProfile) => {
  editingProfile.value = profile
  editName.value = profile.name
}

const cancelEdit = () => {
  editingProfile.value = null
  editName.value = ''
}

const saveEdit = async () => {
  if (!editingProfile.value || !editName.value.trim()) return

  saving.value = true
  try {
    await voiceCloneApi.updateProfile(editingProfile.value.id, editName.value.trim())
    // 更新本地状态
    const index = profiles.value.findIndex(p => p.id === editingProfile.value!.id)
    if (index !== -1) {
      profiles.value[index].name = editName.value.trim()
    }
    cancelEdit()
  } catch (e) {
    alert('Failed to save')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold text-gray-900">Voice Profiles</h2>
      <RouterLink to="/studio" class="btn-primary text-sm">
        Add New Voice
      </RouterLink>
    </div>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="animate-pulse flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
        <div class="w-16 h-16 bg-gray-200 rounded-full"></div>
        <div class="flex-1">
          <div class="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div class="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    </div>

    <div v-else-if="profiles.length === 0" class="text-center py-12">
      <div class="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <img src="/icons/icon-microphone.png" alt="" class="w-10 h-10 object-contain" />
      </div>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">No Voice Profiles Yet</h3>
      <p class="text-gray-500 mb-4">Create your first voice profile to start telling stories</p>
      <RouterLink to="/studio" class="btn-primary">
        Create Voice Profile
      </RouterLink>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
      >
        <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
          <img src="/icons/icon-microphone.png" alt="" class="w-8 h-8 object-contain" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-900">{{ profile.name }}</h3>
          <p class="text-sm text-gray-500">Created {{ new Date(profile.created_at).toLocaleDateString() }}</p>
        </div>
        <audio
          v-if="profile.preview_audio_url"
          :src="profile.preview_audio_url"
          controls
          class="w-48 flex-shrink-0"
        ></audio>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            @click="startEdit(profile)"
            class="p-2 text-gray-400 hover:text-primary-500 transition-colors"
            title="Edit name"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </button>
          <button
            @click="deleteProfile(profile.id)"
            class="p-2 text-gray-400 hover:text-red-500 transition-colors"
            title="Delete"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div v-if="editingProfile" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
          <h3 class="text-lg font-bold text-gray-900 mb-4">Edit Voice Profile</h3>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Profile Name</label>
            <input
              v-model="editName"
              type="text"
              class="input"
              placeholder="Enter profile name"
              @keyup.enter="saveEdit"
            />
          </div>
          <div class="flex justify-end gap-3">
            <button @click="cancelEdit" class="btn-secondary">Cancel</button>
            <button @click="saveEdit" :disabled="saving || !editName.trim()" class="btn-primary">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
