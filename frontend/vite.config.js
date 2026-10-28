import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        graphicMethod: fileURLToPath(new URL('./graphic-method.html', import.meta.url)),
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
})
