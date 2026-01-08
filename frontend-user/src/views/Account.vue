<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api'

const userStore = useUserStore()

const nickname = ref(userStore.user?.nickname || '')
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)
const changingPassword = ref(false)
const message = ref('')
const error = ref('')

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
          <div>
            <p class="font-medium text-gray-900">{{ userStore.user?.email }}</p>
            <label class="text-sm text-primary-500 hover:underline cursor-pointer">
              <input type="file" accept="image/*" class="hidden" />
              Change Avatar
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
    </div>
  </div>
</template>
