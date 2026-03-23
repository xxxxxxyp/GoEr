import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 确保监听所有网卡
    allowedHosts: [
      'airlines-castle-sharing-injection.trycloudflare.com', // 允许当前的 Cloudflare 域名
      '.trycloudflare.com' // 或者使用通配符允许所有 Cloudflare 临时域名
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 转发到后端
        changeOrigin: true, // 必须为 true，否则后端可能拒绝来自外网域名的请求
      },
    },
  },
})
