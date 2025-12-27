import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')

  const port = parseInt(env.VITE_PORT || '3001')
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0', // 监听所有网卡，允许外网访问
      port: port,
      allowedHosts: ['localhost', '.ngrok-free.app'],
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true
        },
        '/uploads': {
          target: apiBaseUrl,
          changeOrigin: true
        }
      }
    }
  }
})
