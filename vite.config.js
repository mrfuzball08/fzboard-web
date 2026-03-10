import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
    svelte(),
  ],
  build: {
    // Output to Django's static directory so collectstatic can pick it up
    outDir: 'static/dist',
    emptyOutDir: true,
    // Generate a manifest so django-vite can resolve hashed filenames
    manifest: true,
    rollupOptions: {
      input: 'frontend/src/main.js',
    },
  },
  server: {
    // Dev server settings for the Docker container
    host: '0.0.0.0',
    port: 5173,
    // Allow requests from the Django dev server origin
    cors: true,
  },
})
