<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { userApi, voiceCloneApi, digitalHumanApi } from '@/api'

const userStore = useUserStore()

const nickname = ref(userStore.user?.nickname || '')
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)
const changingPassword = ref(false)
const uploadingAvatar = ref(false)
const message = ref('')
const error = ref('')

// 档案统计
const voiceProfileCount = ref(0)
const avatarProfileCount = ref(0)

onMounted(async () => {
  // 加载档案数量
  try {
    const [voiceRes, avatarRes] = await Promise.all([
      voiceCloneApi.getProfiles(),
      digitalHumanApi.getProfiles()
    ])
    voiceProfileCount.value = voiceRes.data.total || voiceRes.data.profiles?.length || 0
    avatarProfileCount.value = avatarRes.data.total || avatarRes.data.profiles?.length || 0
  } catch (e) {
    console.error('Failed to load profile counts', e)
  }
})

const handleAvatarUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadingAvatar.value = true
  message.value = ''
  error.value = ''
  try {
    const res = await userApi.uploadAvatar(file)
    // 更新 store 中的用户信息
    if (userStore.user) {
      userStore.user.avatar_url = res.data.avatar_url
    }
    message.value = 'Avatar updated successfully'
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Failed to upload avatar'
  } finally {
    uploadingAvatar.value = false
  }
}

const saveProfile = async () => {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    await userStore.updateProfile({ nickname: nickname.value })
    message.value = 'Profile saved successfully'
  } catch (e) {
    error.value = 'Failed to save, please try again'
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  if (newPassword.value.length < 6) {
    error.value = 'New password must be at least 6 characters'
    return
  }

  changingPassword.value = true
  message.value = ''
  error.value = ''
  try {
    await userApi.changePassword(oldPassword.value, newPassword.value)
    message.value = 'Password changed successfully'
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Failed to change password'
  } finally {
    changingPassword.value = false
  }
}

const getPlanDisplayName = (plan: string) => {
  const names: Record<string, string> = {
    free: 'Free',
    basic: 'Basic',
    premium: 'Premium'
  }
  return names[plan] || plan
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>

      <!-- Messages -->
      <div v-if="message" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700">
        {{ message }}
      </div>
      <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
        {{ error }}
      </div>

      <!-- Profile Section -->
      <div class="bg-white rounded-2xl shadow-soft p-6 mb-6">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Profile</h2>

        <div class="flex items-center gap-6 mb-6">
          <div class="relative">
            <div class="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center text-3xl overflow-hidden">
              <img
                v-if="userStore.user?.avatar_url"
                :src="userStore.user.avatar_url"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-primary-500 font-bold">
                {{ userStore.user?.nickname?.[0] || 'U' }}
              </span>
            </div>
            <div v-if="uploadingAvatar" class="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center">
              <div class="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            </div>
          </div>
          <div>
            <p class="font-medium text-gray-900">{{ userStore.user?.email }}</p>
            <label class="text-sm text-primary-500 hover:underline cursor-pointer">
              <input
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleAvatarUpload"
                :disabled="uploadingAvatar"
              />
              {{ uploadingAvatar ? 'Uploading...' : 'Change Avatar' }}
            </label>
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Nickname</label>
            <input
              v-model="nickname"
              type="text"
              class="input"
              placeholder="Your nickname"
            />
          </div>

          <button
            @click="saveProfile"
            :disabled="saving"
            class="btn-primary"
          >
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>

      <!-- Quick Links to Profiles -->
      <div class="bg-white rounded-2xl shadow-soft p-6 mb-6">
        <h2 class="text-xl font-bold text-gray-900 mb-6">My Profiles</h2>
        <div class="grid grid-cols-2 gap-4">
          <RouterLink
            to="/profiles/voice"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <img src="/icons/icon-microphone.png" alt="" class="w-6 h-6 object-contain" />
            </div>
            <div>
              <p class="font-medium text-gray-900">Voice Profiles</p>
              <p class="text-sm text-gray-500">{{ voiceProfileCount }} profiles</p>
            </div>
          </RouterLink>

          <RouterLink
            to="/profiles/avatar"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <img src="/icons/icon-avatar.png" alt="" class="w-6 h-6 object-contain" />
            </div>
            <div>
              <p class="font-medium text-gray-900">Avatar Profiles</p>
              <p class="text-sm text-gray-500">{{ avatarProfileCount }} profiles</p>
            </div>
          </RouterLink>
        </div>

        <RouterLink
          to="/profiles/creations"
          class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors mt-4"
        >
          <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
            <img src="/icons/icon-sparkles.png" alt="" class="w-6 h-6 object-contain" />
          </div>
          <div>
            <p class="font-medium text-gray-900">My Creations</p>
            <p class="text-sm text-gray-500">View generated videos</p>
          </div>
        </RouterLink>
      </div>

      <!-- Password Section -->
      <div class="bg-white rounded-2xl shadow-soft p-6">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Change Password</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
            <input
              v-model="oldPassword"
              type="password"
              class="input"
              placeholder="Enter current password"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">New Password</label>
            <input
              v-model="newPassword"
              type="password"
              class="input"
              placeholder="Enter new password"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="input"
              placeholder="Re-enter new password"
            />
          </div>

          <button
            @click="changePassword"
            :disabled="changingPassword"
            class="btn-primary"
          >
            {{ changingPassword ? 'Changing...' : 'Change Password' }}
          </button>
        </div>
      </div>

      <!-- Subscription Info -->
      <RouterLink
        to="/subscription"
        class="block bg-white rounded-2xl shadow-soft p-6 mt-6 hover:shadow-md transition-shadow cursor-pointer"
      >
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-900 mb-1">Subscription</h2>
            <p class="font-medium text-gray-700 capitalize">
              {{ getPlanDisplayName(userStore.user?.subscription?.plan || 'free') }} Plan
            </p>
            <p class="text-sm text-gray-500">
              <template v-if="userStore.user?.subscription?.expires_at">
                Expires: {{ new Date(userStore.user.subscription.expires_at).toLocaleDateString() }}
              </template>
              <template v-else>
                No expiration
              </template>
            </p>
          </div>
          <div class="flex items-center gap-3">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="userStore.user?.subscription?.plan === 'free'
                ? 'bg-gray-100 text-gray-700'
                : 'bg-primary-100 text-primary-700'"
            >
              Active
            </span>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
