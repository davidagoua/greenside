import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  ssr: true,
  modules: [
    '@nuxtjs/tailwindcss',
    '@vite-pwa/nuxt'
  ],
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
      openinaryUrl: process.env.NUXT_PUBLIC_OPENINARY_URL || 'http://localhost:8080'
    }
  },
  css: [
    'leaflet/dist/leaflet.css',
    '~/assets/css/main.css'
  ],
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'EcoLoop - Circular Hub',
      short_name: 'EcoLoop',
      description: 'Marketplace circulaire B2B/B2C pour la valorisation des déchets recyclables',
      theme_color: '#059669',
      background_color: '#0f172a',
      display: 'standalone',
      orientation: 'portrait',
      icons: [
        {
          src: '/icons/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico}'],
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/.*tile\.openstreetmap\.org\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'osm-tiles-cache',
            expiration: {
              maxEntries: 500,
              maxAgeSeconds: 60 * 60 * 24 * 30 // 30 jours
            },
            cacheableResponse: {
              statuses: [0, 200]
            }
          }
        },
        {
          urlPattern: /\/api\/v1\/listings.*/i,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'listings-api-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 2 // 2 heures
            },
            cacheableResponse: {
              statuses: [0, 200]
            }
          }
        }
      ]
    },
    devOptions: {
      enabled: false
    }
  },
  app: {
    head: {
      title: 'EcoLoop — Circular Hub',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        { name: 'theme-color', content: '#059669' },
        { name: 'description', content: 'Marketplace circulaire B2B/B2C pour la collecte et valorisation des déchets' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  }
})
