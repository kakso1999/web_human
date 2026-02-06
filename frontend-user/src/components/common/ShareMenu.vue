<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  url: string
  title: string
  description?: string
  imageUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  imageUrl: ''
})

const emit = defineEmits(['close'])

const showMenu = ref(false)
const copySuccess = ref(false)

// 编码分享内容
const encodedUrl = computed(() => encodeURIComponent(props.url))
const encodedTitle = computed(() => encodeURIComponent(props.title))
const encodedDescription = computed(() => encodeURIComponent(props.description || props.title))

// 社交媒体分享链接
const shareLinks = computed(() => [
  {
    name: 'WhatsApp',
    icon: 'whatsapp',
    color: '#25D366',
    url: `https://wa.me/?text=${encodedTitle.value}%0A${encodedUrl.value}`
  },
  {
    name: 'Telegram',
    icon: 'telegram',
    color: '#0088cc',
    url: `https://t.me/share/url?url=${encodedUrl.value}&text=${encodedTitle.value}`
  },
  {
    name: 'WeChat',
    icon: 'wechat',
    color: '#07C160',
    action: 'wechat' // 微信需要特殊处理
  },
  {
    name: 'Facebook',
    icon: 'facebook',
    color: '#1877F2',
    url: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl.value}&quote=${encodedTitle.value}`
  },
  {
    name: 'X (Twitter)',
    icon: 'twitter',
    color: '#000000',
    url: `https://twitter.com/intent/tweet?url=${encodedUrl.value}&text=${encodedTitle.value}`
  },
  {
    name: 'LinkedIn',
    icon: 'linkedin',
    color: '#0A66C2',
    url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl.value}`
  },
  {
    name: 'Reddit',
    icon: 'reddit',
    color: '#FF4500',
    url: `https://www.reddit.com/submit?url=${encodedUrl.value}&title=${encodedTitle.value}`
  },
  {
    name: 'Pinterest',
    icon: 'pinterest',
    color: '#E60023',
    url: `https://pinterest.com/pin/create/button/?url=${encodedUrl.value}&description=${encodedTitle.value}&media=${encodeURIComponent(props.imageUrl)}`
  },
  {
    name: 'Email',
    icon: 'email',
    color: '#EA4335',
    url: `mailto:?subject=${encodedTitle.value}&body=${encodedDescription.value}%0A%0A${encodedUrl.value}`
  }
])

// 显示微信二维码
const showWeChatQR = ref(false)

const handleShare = (link: typeof shareLinks.value[0]) => {
  if (link.action === 'wechat') {
    showWeChatQR.value = true
  } else if (link.url) {
    window.open(link.url, '_blank', 'width=600,height=400')
  }
  showMenu.value = false
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(props.url)
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
  emit('close')
}

// 使用 Web Share API (移动端)
const canUseNativeShare = computed(() => !!navigator.share)

const nativeShare = async () => {
  try {
    await navigator.share({
      title: props.title,
      text: props.description || props.title,
      url: props.url
    })
  } catch (e) {
    // 用户取消或不支持
    console.log('Share cancelled or failed:', e)
  }
}
</script>

<template>
  <div class="share-menu-container relative">
    <!-- 分享按钮 -->
    <button
      @click="toggleMenu"
      class="share-btn p-2 text-gray-500 hover:text-primary-500 rounded-lg hover:bg-gray-200 transition-all"
      title="Share"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/>
      </svg>
    </button>

    <!-- 下拉菜单 -->
    <Teleport to="body">
      <div v-if="showMenu" class="fixed inset-0 z-50" @click="closeMenu">
        <div class="absolute inset-0 bg-black/30" />
        <div
          class="share-dropdown fixed bottom-0 left-0 right-0 md:absolute md:bottom-auto md:left-auto md:right-auto md:top-auto bg-white rounded-t-2xl md:rounded-xl shadow-2xl p-4 md:p-3 animate-slide-up md:animate-fade-in md:w-80"
          :style="{ maxHeight: '80vh' }"
          @click.stop
        >
          <!-- 标题 -->
          <div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
            <h3 class="font-semibold text-gray-900">Share to</h3>
            <button @click="closeMenu" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- 原生分享 (移动端优先) -->
          <button
            v-if="canUseNativeShare"
            @click="nativeShare"
            class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors mb-2"
          >
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
              </svg>
            </div>
            <span class="font-medium text-gray-900">More options...</span>
          </button>

          <!-- 社交媒体网格 -->
          <div class="grid grid-cols-4 gap-2 mb-4">
            <button
              v-for="link in shareLinks"
              :key="link.name"
              @click="handleShare(link)"
              class="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-gray-50 transition-colors"
            >
              <div
                class="w-12 h-12 rounded-full flex items-center justify-center"
                :style="{ backgroundColor: link.color + '15' }"
              >
                <!-- WhatsApp -->
                <svg v-if="link.icon === 'whatsapp'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                <!-- Telegram -->
                <svg v-else-if="link.icon === 'telegram'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                <!-- WeChat -->
                <svg v-else-if="link.icon === 'wechat'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.27-.027-.407-.032zM13.12 12.06c.536 0 .97.44.97.983a.976.976 0 0 1-.97.983.976.976 0 0 1-.97-.983c0-.542.434-.983.97-.983zm4.854 0c.536 0 .97.44.97.983a.976.976 0 0 1-.97.983.976.976 0 0 1-.97-.983c0-.542.434-.983.97-.983z"/>
                </svg>
                <!-- Facebook -->
                <svg v-else-if="link.icon === 'facebook'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                <!-- Twitter/X -->
                <svg v-else-if="link.icon === 'twitter'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/>
                </svg>
                <!-- LinkedIn -->
                <svg v-else-if="link.icon === 'linkedin'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                <!-- Reddit -->
                <svg v-else-if="link.icon === 'reddit'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                </svg>
                <!-- Pinterest -->
                <svg v-else-if="link.icon === 'pinterest'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/>
                </svg>
                <!-- Email -->
                <svg v-else-if="link.icon === 'email'" class="w-6 h-6" :style="{ color: link.color }" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"/>
                </svg>
              </div>
              <span class="text-xs text-gray-600 text-center leading-tight">{{ link.name }}</span>
            </button>
          </div>

          <!-- 复制链接 -->
          <button
            @click="copyLink"
            class="w-full flex items-center justify-center gap-2 p-3 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
          >
            <svg v-if="!copySuccess" class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/>
            </svg>
            <svg v-else class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span class="font-medium" :class="copySuccess ? 'text-green-600' : 'text-gray-700'">
              {{ copySuccess ? 'Copied!' : 'Copy Link' }}
            </span>
          </button>
        </div>
      </div>
    </Teleport>

    <!-- 微信二维码弹窗 -->
    <Teleport to="body">
      <div
        v-if="showWeChatQR"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click="showWeChatQR = false"
      >
        <div class="bg-white rounded-2xl p-6 max-w-sm mx-4 text-center" @click.stop>
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
            <svg class="w-8 h-8 text-green-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18z"/>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Share to WeChat</h3>
          <p class="text-sm text-gray-500 mb-4">Copy the link and paste it in WeChat to share with your friends</p>
          <button
            @click="copyLink(); showWeChatQR = false"
            class="w-full py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-xl transition-colors"
          >
            Copy Link
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}
</style>
