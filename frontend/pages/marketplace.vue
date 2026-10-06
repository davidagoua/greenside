<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Top Filter & Controls -->
    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 mb-6 shadow-xl">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Matière / Catégorie</label>
          <select
            v-model="selectedCategory"
            @change="fetchListings"
            class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-eco-500 transition"
          >
            <option value="">Toutes les matières</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.slug">
              {{ cat.name }} ({{ cat.unit }})
            </option>
          </select>
        </div>

        <div>
          <div class="flex justify-between items-center mb-1.5">
            <label class="text-xs font-semibold text-slate-300">Rayon géographique</label>
            <span class="text-xs font-bold text-eco-400 font-mono">{{ radiusKm }} km</span>
          </div>
          <input
            v-model.number="radiusKm"
            @change="fetchListings"
            type="range"
            min="5"
            max="150"
            step="5"
            class="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-eco-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Position centrale (GPS)</label>
          <div class="flex space-x-2">
            <input
              v-model.number="centerLat"
              type="number"
              step="0.001"
              placeholder="Lat"
              class="w-1/2 px-2.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs font-mono"
            />
            <input
              v-model.number="centerLng"
              type="number"
              step="0.001"
              placeholder="Lng"
              class="w-1/2 px-2.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs font-mono"
            />
          </div>
        </div>

        <div class="flex space-x-2">
          <button
            @click="useCurrentLocation"
            type="button"
            class="flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center space-x-1.5"
          >
            <svg class="w-4 h-4 text-eco-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            </svg>
            <span>Me localiser</span>
          </button>

          <button
            @click="fetchListings"
            type="button"
            class="px-4 py-2.5 rounded-xl bg-eco-600 hover:bg-eco-500 text-white text-xs font-bold transition shadow-lg shadow-eco-600/20"
          >
            Filtrer
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content: Map + synchronized listings list -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Interactive Leaflet Map (7 cols on large screens) -->
      <div class="lg:col-span-7 h-[420px] lg:h-[650px] sticky top-24">
        <ClientOnly>
          <MarketMap
            :center-lat="centerLat"
            :center-lng="centerLng"
            :radius-km="radiusKm"
            :listings="listings"
            @select-listing="handleSelectListing"
          />
          <template #fallback>
            <div class="w-full h-full rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center">
              <span class="text-xs text-slate-500">Chargement de la carte...</span>
            </div>
          </template>
        </ClientOnly>
      </div>

      <!-- Synchronized Listings List (5 cols) -->
      <div class="lg:col-span-5 space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-slate-800">
          <h2 class="text-sm font-bold uppercase tracking-wider text-slate-400">
            Gisements disponibles ({{ listings.length }})
          </h2>
          <span class="text-xs text-eco-400 font-medium">Classés par proximité</span>
        </div>

        <div v-if="loading" class="py-12 flex justify-center">
          <div class="w-8 h-8 border-4 border-eco-500 border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="listings.length === 0" class="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center">
          <p class="text-sm text-slate-400">Aucun gisement trouvé dans ce rayon.</p>
          <p class="text-xs text-slate-500 mt-1">Élargissez le rayon de recherche ou changez de matière.</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="item in listings"
            :key="item.id"
            :id="`listing-card-${item.id}`"
            class="p-4 rounded-2xl bg-slate-900 border transition hover:border-eco-500/50 cursor-pointer"
            :class="selectedListingId === item.id ? 'border-eco-500 bg-slate-850' : 'border-slate-800'"
            @click="selectedListingId = item.id"
          >
            <div class="flex gap-4">
              <!-- Thumbnail -->
              <div class="w-20 h-20 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden shrink-0">
                <img
                  v-if="item.thumbnail_url"
                  :src="item.thumbnail_url"
                  :alt="item.title"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-slate-600 text-[10px]">
                  Pas d'image
                </div>
              </div>

              <!-- Details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between">
                  <h3 class="text-sm font-bold text-white truncate pr-2">{{ item.title }}</h3>
                  <span class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-eco-400 shrink-0">
                    {{ item.distance_km.toFixed(1) }} km
                  </span>
                </div>

                <div class="flex items-center space-x-2 mt-1">
                  <span class="text-xs font-semibold text-slate-200">
                    {{ item.estimated_quantity }} {{ item.unit }}
                  </span>
                  <span class="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {{ item.category_name }}
                  </span>
                </div>

                <p class="text-xs text-slate-400 truncate mt-1">📍 {{ item.address_text }}</p>

                <div class="mt-3 flex items-center justify-between">
                  <div class="text-xs font-bold" :class="item.is_free_donation ? 'text-amber-400' : 'text-eco-400'">
                    {{ item.is_free_donation ? 'Don gratuit' : `${item.price_per_unit} FCFA / ${item.unit}` }}
                  </div>

                  <button
                    v-if="user?.role === 'collector'"
                    @click.stop="openReserveModal(item)"
                    type="button"
                    class="px-3 py-1.5 rounded-lg bg-eco-600 hover:bg-eco-500 text-white text-xs font-semibold transition shadow-md shadow-eco-600/20"
                  >
                    Réserver
                  </button>
                  <NuxtLink
                    v-else
                    :to="`/marketplace`"
                    class="text-xs text-slate-400 hover:text-white"
                  >
                    Voir détails
                  </NuxtLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reservation Modal for Collectors -->
    <div v-if="reservingListing" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
        <h3 class="text-lg font-bold text-white">Confirmer la réservation & séquestre</h3>
        <p class="text-xs text-slate-400 mt-1">
          Gisement : <b class="text-slate-200">{{ reservingListing.title }}</b>
        </p>

        <div class="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
          <div class="flex justify-between">
            <span class="text-slate-400">Quantité disponible :</span>
            <span class="font-semibold text-white">{{ reservingListing.estimated_quantity }} {{ reservingListing.unit }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Prix unitaire :</span>
            <span class="font-semibold text-white">
              {{ reservingListing.is_free_donation ? '0 (Don)' : reservingListing.price_per_unit + ' FCFA' }}
            </span>
          </div>
          <div class="flex justify-between border-t border-slate-800 pt-2 font-bold">
            <span class="text-eco-400">Montant total séquestré :</span>
            <span class="text-eco-400">
              {{ (reservingListing.estimated_quantity * (reservingListing.is_free_donation ? 0 : reservingListing.price_per_unit)).toLocaleString() }} FCFA
            </span>
          </div>
        </div>

        <div class="mt-6 flex space-x-3">
          <button
            @click="reservingListing = null"
            type="button"
            class="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Annuler
          </button>
          <button
            @click="confirmReservation"
            :disabled="actionLoading"
            type="button"
            class="flex-1 py-2.5 rounded-xl bg-eco-600 hover:bg-eco-500 text-white text-xs font-semibold transition shadow-lg shadow-eco-600/20 disabled:opacity-50"
          >
            {{ actionLoading ? 'Verrouillage séquestre...' : 'Confirmer séquestre' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { NearbyListing, WasteCategory } from '~/types'

const { user } = useAuth()
const { apiFetch } = useApi()

const categories = ref<WasteCategory[]>([])
const listings = ref<NearbyListing[]>([])
const loading = ref(false)
const actionLoading = ref(false)

const selectedCategory = ref('')
const radiusKm = ref(30)
const centerLat = ref(14.7167) // Dakar default
const centerLng = ref(-17.4677)
const selectedListingId = ref<string | null>(null)
const reservingListing = ref<NearbyListing | null>(null)

const fetchCategories = async () => {
  try {
    categories.value = await apiFetch<WasteCategory[]>('/categories')
  } catch (err) {
    console.error('Erreur chargement catégories:', err)
  }
}

const fetchListings = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      lat: centerLat.value,
      lng: centerLng.value,
      radius_km: radiusKm.value
    }
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }
    listings.value = await apiFetch<NearbyListing[]>('/listings/nearby', { params })
  } catch (err) {
    console.error('Erreur chargement listings:', err)
  } finally {
    loading.value = false
  }
}

const useCurrentLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        centerLat.value = parseFloat(pos.coords.latitude.toFixed(4))
        centerLng.value = parseFloat(pos.coords.longitude.toFixed(4))
        fetchListings()
      },
      (err) => {
        alert("Impossible d'obtenir votre position GPS: " + err.message)
      }
    )
  }
}

const handleSelectListing = (item: NearbyListing) => {
  selectedListingId.value = item.id
  const el = document.getElementById(`listing-card-${item.id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
}

const openReserveModal = (item: NearbyListing) => {
  reservingListing.value = item
}

const confirmReservation = async () => {
  if (!reservingListing.value) return
  actionLoading.value = true
  try {
    const res = await apiFetch<any>('/transactions/reserve', {
      method: 'POST',
      body: {
        listing_id: reservingListing.value.id,
        agreed_quantity: reservingListing.value.estimated_quantity
      }
    })
    reservingListing.value = null
    navigateTo(`/transactions/${res.id}`)
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur lors de la réservation')
  } finally {
    actionLoading.value = false
  }
}

onMounted(async () => {
  await fetchCategories()
  await fetchListings()
})
</script>
