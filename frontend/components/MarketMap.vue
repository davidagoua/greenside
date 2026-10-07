<template>
  <div class="relative w-full h-full min-h-[400px] border border-cds-border-subtle overflow-hidden">
    <div ref="mapContainer" class="w-full h-full min-h-[400px] z-0"></div>

    <!-- Recentrer sur la position de recherche -->
    <button
      type="button"
      class="absolute bottom-4 right-4 z-10 cds--btn cds--btn--secondary cds--btn--sm"
      title="Recentrer la carte"
      aria-label="Recentrer la carte"
      @click="recenter"
    >
      <Lineicons :icon="Icons.location" :size="18" color="currentColor" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { NearbyListing } from '~/types'

// Icônes de marqueur servies par le bundle (et non par un CDN tiers) :
// indispensable pour que la carte fonctionne hors ligne en PWA.
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const props = defineProps<{
  centerLat: number
  centerLng: number
  radiusKm: number
  listings: NearbyListing[]
}>()

const emit = defineEmits<{
  (e: 'select-listing', listing: NearbyListing): void
}>()

const { isDark } = useTheme()

const mapContainer = ref<HTMLElement | null>(null)
let mapInstance: any = null
let markersLayer: any = null
let circleLayer: any = null
let tileLayer: any = null
let leaflet: any = null

/** Fond de carte adapté au thème (CARTO, même fournisseur que la règle workbox). */
const tileUrl = () =>
  isDark.value
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'

/**
 * Leaflet écrit les couleurs en attributs SVG : `var(--cds-*)` n'y est pas
 * résolu. On lit donc la valeur calculée du jeton pour les tracés canvas/SVG.
 */
const token = (name: string, fallback: string): string => {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const escapeHtml = (value: unknown): string =>
  String(value ?? '').replace(/[&<>"']/g, (char) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char] as string
  )

const initMap = async () => {
  if (typeof window === 'undefined' || !mapContainer.value) return
  const L = (await import('leaflet')).default
  leaflet = L

  // Icônes de marqueur résolues par le bundler
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow
  })

  mapInstance = L.map(mapContainer.value).setView([props.centerLat, props.centerLng], 12)

  tileLayer = L.tileLayer(tileUrl(), {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
    maxZoom: 19
  }).addTo(mapInstance)

  markersLayer = L.layerGroup().addTo(mapInstance)
  circleLayer = L.layerGroup().addTo(mapInstance)

  updateCircle()
  updateMarkers()
}

const updateCircle = () => {
  if (!circleLayer || !mapInstance || !leaflet) return
  circleLayer.clearLayers()

  const stroke = token('--cds-support-success', '#24a148')

  leaflet
    .circle([props.centerLat, props.centerLng], {
      color: stroke,
      fillColor: stroke,
      fillOpacity: 0.12,
      radius: props.radiusKm * 1000
    })
    .addTo(circleLayer)
}

const updateMarkers = () => {
  if (!markersLayer || !mapInstance || !leaflet) return
  markersLayer.clearLayers()

  props.listings.forEach((listing) => {
    const marker = leaflet.marker([listing.lat, listing.lng]).addTo(markersLayer)

    // Les couleurs utilisent les jetons Carbon : la popup suit le thème actif.
    const price = listing.is_free_donation
      ? 'Don gratuit'
      : `${escapeHtml(listing.price_per_unit)} FCFA / ${escapeHtml(listing.unit)}`

    const popupContent = `
      <div style="font-family: 'IBM Plex Sans', system-ui, sans-serif; font-size: 13px; color: var(--cds-text-primary); padding: 2px;">
        <p style="font-weight: 600; margin-bottom: 4px;">${escapeHtml(listing.title)}</p>
        <p style="margin-bottom: 2px; color: var(--cds-text-secondary);">
          <b style="color: var(--cds-text-primary);">${escapeHtml(listing.estimated_quantity)} ${escapeHtml(listing.unit)}</b>
          &middot; ${escapeHtml(listing.category_name)}
        </p>
        <p style="margin-bottom: 4px; color: var(--cds-link-primary); font-weight: 600;">${price}</p>
        <p style="font-size: 11px; color: var(--cds-text-helper);">
          ${escapeHtml(listing.distance_km?.toFixed(1) ?? '—')} km
        </p>
      </div>
    `
    marker.bindPopup(popupContent)
    marker.on('click', () => {
      emit('select-listing', listing)
    })
  })
}

const recenter = () => {
  if (!mapInstance) return
  mapInstance.setView([props.centerLat, props.centerLng], 12)
}

onMounted(() => {
  initMap()
})

onBeforeUnmount(() => {
  // Sans destroy(), l'instance Leaflet et ses écouteurs fuient à chaque navigation
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
  markersLayer = null
  circleLayer = null
  tileLayer = null
  leaflet = null
})

watch(
  () => [props.centerLat, props.centerLng, props.radiusKm],
  () => {
    if (!mapInstance) return
    mapInstance.setView([props.centerLat, props.centerLng])
    updateCircle()
  }
)

watch(
  () => props.listings,
  () => {
    updateMarkers()
  },
  { deep: true }
)

// Bascule du fond de carte et des tracés quand l'utilisateur change de thème
watch(isDark, () => {
  if (tileLayer) tileLayer.setUrl(tileUrl())
  updateCircle()
  updateMarkers()
})
</script>
