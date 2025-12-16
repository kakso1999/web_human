<template>
  <div class="profile-page">
    <div class="profile-container">
      <button class="back-btn" @click="goBack">返回</button>

      <h1 class="profile-title">个人信息</h1>

      <div class="profile-content">
        <!-- 头像 -->
        <div class="avatar-section">
          <img
            :src="user?.avatar_url || '/default-avatar.svg'"
            alt="avatar"
            class="avatar-preview"
          />
          <input
            type="file"
            ref="fileInput"
            accept="image/*"
            @change="handleAvatarUpload"
            hidden
          />
          <button class="btn btn-primary" @click="triggerFileInput">更换头像</button>
        </div>

        <!-- 表单 -->
        <form class="profile-form" @submit.prevent="handleSave">
          <div class="form-group">
            <label>邮箱</label>
            <input type="email" class="input" :value="user?.email" disabled />
          </div>

          <div class="form-group">
            <label>昵称</label>
            <input
              v-model="nickname"
              type="text"
              class="input"
              placeholder="输入昵称"
            />
          </div>

          <p v-if="message" :class="['message', messageType]">{{ message }}</p>

          <button type="submit" class="btn btn-accent" :disabled="saving">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </form>

        <!-- 修改密码 -->
        <div class="password-section">
          <h2>修改密码</h2>
          <form @submit.prevent="handleChangePassword">
            <div class="form-group">
              <label>原密码</label>
              <input v-model="oldPassword" type="password" class="input" />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input v-model="newPassword" type="password" class="input" />
            </div>
            <button type="submit" class="btn btn-primary" :disabled="changingPassword">
              {{ changingPassword ? '修改中...' : '修改密码' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const nickname = ref('')
const fileInput = ref<HTMLInputElement>()

const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const saving = ref(false)

const oldPassword = ref('')
const newPassword = ref('')
const changingPassword = ref(false)

function goBack() {
  router.push('/dashboard')
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleAvatarUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.[0]) return

  const formData = new FormData()
  formData.append('file', input.files[0])

  try {
    const response = await api.post('/user/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    await userStore.fetchProfile()
    showMessage('头像更新成功', 'success')
  } catch (error: any) {
    showMessage(error.response?.data?.message || '上传失败', 'error')
  }
}

async function handleSave() {
  saving.value = true
  try {
    await userStore.updateProfile({ nickname: nickname.value })
    showMessage('保存成功', 'success')
  } catch (error: any) {
    showMessage(error.response?.data?.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function handleChangePassword() {
  if (!oldPassword.value || !newPassword.value) {
    showMessage('请填写完整', 'error')
    return
  }

  changingPassword.value = true
  try {
    await api.post('/user/change-password', {
      old_password: oldPassword.value,
      new_password: newPassword.value
    })
    showMessage('密码修改成功', 'success')
    oldPassword.value = ''
    newPassword.value = ''
  } catch (error: any) {
    showMessage(error.response?.data?.message || '修改失败', 'error')
  } finally {
    changingPassword.value = false
  }
}

function showMessage(msg: string, type: 'success' | 'error') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

onMounted(async () => {
  await userStore.fetchProfile()
  nickname.value = user.value?.nickname || ''
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: var(--spacing-xl);
}

.profile-container {
  max-width: 600px;
  margin: 0 auto;
}

.back-btn {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
}

.profile-title {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--spacing-xl);
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.message {
  font-size: var(--font-size-sm);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.message.success {
  background: rgba(52, 199, 89, 0.2);
  color: var(--color-success);
}

.message.error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
}

.password-section {
  padding-top: var(--spacing-xl);
  border-top: 1px solid var(--color-border);
}

.password-section h2 {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-md);
}

.password-section form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
</style>
