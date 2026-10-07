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
    // Design system Carbon : jetons (--cds-*) + styles des composants (cds--*).
    // Doit précéder main.css pour que les surcharges de l'application gagnent.
    '@carbon/styles/css/styles.css',
    'leaflet/dist/leaflet.css',
    '~/assets/css/main.css'
  ],
  features: {
    /**
     * Nuxt inline par défaut les styles d'entrée dans le HTML SSR. Avec Carbon
     * (≈1 Mo de CSS) cela produisait ~1 Mo de HTML non cacheable par page.
     * On émet à la place une feuille de style externe, mise en cache par le
     * navigateur et précachée par le service worker.
     */
    inlineStyles: false
  },
  build: {
    /**
     * Lineicons est publié sans champ `exports` et uniquement en ESM/CJS
     * minifié : externalisé par Nitro, Node ne sait pas en résoudre les exports
     * nommés au runtime (500 en SSR). On force donc son inclusion dans les
     * bundles client et serveur.
     */
    transpile: ['@lineiconshq/vue-lineicons', '@lineiconshq/free-icons']
  },
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'EcoLoop - Circular Hub',
      short_name: 'EcoLoop',
      description: 'Marketplace circulaire B2B/B2C pour la valorisation des déchets recyclables',
      theme_color: '#0f62fe',
      background_color: '#ffffff',
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
      // woff2 ajouté : la typographie IBM Plex est auto-hébergée (hors ligne)
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
      runtimeCaching: [
        {
          // Tuiles réellement utilisées par MarketMap (CARTO, et non OSM)
          urlPattern: /^https:\/\/.*basemaps\.cartocdn\.com\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'map-tiles-cache',
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
        { name: 'theme-color', content: '#0f62fe' },
        { name: 'description', content: 'Marketplace circulaire B2B/B2C pour la collecte et valorisation des déchets' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  }
})
