// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [
    vue(),
    basicSsl(), // ← 自动生成临时证书供前端使用（也可用自己的）
  ],
  server: {
    https: true, // ← 启用 HTTPS
    port: 3000,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'https://127.0.0.1:5000', // ← 注意是 https
        changeOrigin: true,
        secure: false, // 因为是自签名证书，跳过验证
        cookieDomainRewrite: 'localhost',
      },
    },
  },
})
