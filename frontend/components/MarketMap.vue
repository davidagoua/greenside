<template>
  <div class="relative w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-slate-800">
    <div ref="mapContainer" class="w-full h-full min-h-[400px] z-0"></div>

    <!-- Center position button -->
    <button
      @click="recenter"
      type="button"
      class="absolute bottom-4 right-4 z-10 p-3 bg-slate-900/90 hover:bg-slate-800 text-eco-400 border border-slate-700 rounded-xl shadow-lg backdrop-blur transition"
      title="Recentrer la carte"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { NearbyListing } from '~/types'

const props = defineProps<{
  centerLat: number
  centerLng: number
  radiusKm: number
  listings: NearbyListing[]
}>()

const emit = defineEmits<{
  (e: 'select-listing', listing: NearbyListing): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
let mapInstance: any = null
let markersLayer: any = null
let circleLayer: any = null

const initMap = async () => {
  if (typeof window === 'undefined' || !mapContainer.value) return
  const L = (await import('leaflet')).default

  // Fix leaflet default icons in bundlers
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
  })

  mapInstance = L.map(mapContainer.value).setView([props.centerLat, props.centerLng], 12)

  // Dark/Carto tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
    maxZoom: 19
  }).addTo(mapInstance)

  markersLayer = L.layerGroup().addTo(mapInstance)
  circleLayer = L.layerGroup().addTo(mapInstance)

  updateCircle(L)
  updateMarkers(L)
}

const updateCircle = (L: any) => {
  if (!circleLayer || !mapInstance) return
  circleLayer.clearLayers()

  L.circle([props.centerLat, props.centerLng], {
    color: '#059669',
    fillColor: '#10b981',
    fillOpacity: 0.12,
    radius: props.radiusKm * 1000
  }).addTo(circleLayer)
}

const updateMarkers = (L: any) => {
  if (!markersLayer || !mapInstance) return
  markersLayer.clearLayers()

  props.listings.forEach(listing => {
    const marker = L.marker([listing.lat, listing.lng]).addTo(markersLayer)
    
    const popupContent = `
      <div style="font-family: inherit; font-size: 13px; color: #0f172a; padding: 4px;">
        <p style="font-weight: 700; margin-bottom: 4px;">${listing.title}</p>
        <p style="margin-bottom: 2px;">📦 <b>${listing.estimated_quantity} ${listing.unit}</b> (${listing.category_name})</p>
        <p style="margin-bottom: 4px; color: #059669; font-weight: 600;">
          ${listing.is_free_donation ? 'Don gratuit' : listing.price_per_unit + ' FCFA / ' + listing.unit}
        </p>
        <p style="font-size: 11px; color: #64748b;">📍 ${listing.distance_km.toFixed(1)} km</p>
      </div>
    `
    marker.bindPopup(popupContent)
    marker.on('click', () => {
      emit('select-listing', listing)
    })
  })
}

const recenter = async () => {
  if (!mapInstance) return
  mapInstance.setView([props.centerLat, props.centerLng], 12)
}

onMounted(() => {
  initMap()
})

watch(() => [props.centerLat, props.centerLng, props.radiusKm], async () => {
  if (typeof window === 'undefined') return
  const L = (await import('leaflet')).default
  if (mapInstance) {
    mapInstance.setView([props.centerLat, props.centerLng])
    updateCircle(L)
  }
})

watch(() => props.listings, async () => {
  if (typeof window === 'undefined') return
  const L = (await import('leaflet')).default
  updateMarkers(L)
}, { deep: true })
</script>
