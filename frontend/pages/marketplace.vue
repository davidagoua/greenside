<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Panneau de filtres -->
    <div class="bg-cds-layer-01 border border-cds-border-subtle p-5 mb-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div class="cds--form-item">
          <label class="cds--label" for="filtre-matiere">Matière / Catégorie</label>
          <div class="cds--select">
            <div class="cds--select-input__wrapper">
              <select
                id="filtre-matiere"
                v-model="selectedCategory"
                @change="fetchListings"
                class="cds--select-input"
              >
                <option value="">Toutes les matières</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.slug">
                  {{ cat.name }} ({{ cat.unit }})
                </option>
              </select>
              <Lineicons
                class="cds--select__arrow"
                :icon="Icons.expand"
                :size="16"
                color="var(--cds-icon-primary)"
              />
            </div>
          </div>
        </div>

        <div class="cds--form-item">
          <div class="flex justify-between items-center">
            <label class="cds--label" for="filtre-rayon">Rayon géographique</label>
            <span class="text-xs font-bold font-mono text-cds-link-primary">{{ radiusKm }} km</span>
          </div>
          <input
            id="filtre-rayon"
            v-model.number="radiusKm"
            @change="fetchListings"
            type="range"
            min="5"
            max="150"
            step="5"
            class="w-full cursor-pointer accent-[var(--cds-interactive)]"
          />
        </div>

        <div class="cds--form-item">
          <label class="cds--label" for="filtre-lat">Position centrale (GPS)</label>
          <div class="flex space-x-2">
            <div class="w-1/2">
              <input
                id="filtre-lat"
                v-model.number="centerLat"
                type="number"
                step="0.001"
                placeholder="Lat"
                aria-label="Latitude"
                class="cds--text-input font-mono placeholder:text-cds-text-placeholder"
              />
            </div>
            <div class="w-1/2">
              <input
                v-model.number="centerLng"
                type="number"
                step="0.001"
                placeholder="Lng"
                aria-label="Longitude"
                class="cds--text-input font-mono placeholder:text-cds-text-placeholder"
              />
            </div>
          </div>
        </div>

        <div class="flex space-x-2">
          <button
            @click="useCurrentLocation"
            type="button"
            class="cds--btn cds--btn--secondary flex-1"
          >
            <span class="flex items-center space-x-2">
              <Lineicons :icon="Icons.location" :size="16" color="currentColor" />
              <span>Me localiser</span>
            </span>
          </button>

          <button
            @click="fetchListings"
            type="button"
            class="cds--btn cds--btn--primary"
          >
            Filtrer
          </button>
        </div>
      </div>
    </div>

    <!-- Contenu principal : carte + liste synchronisées -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Carte Leaflet interactive (7 colonnes sur grand écran) -->
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
            <div class="w-full h-full bg-cds-layer-01 border border-cds-border-subtle flex items-center justify-center">
              <span class="text-xs text-cds-text-helper">Chargement de la carte...</span>
            </div>
          </template>
        </ClientOnly>
      </div>

      <!-- Liste synchronisée (5 colonnes) -->
      <div class="lg:col-span-5 space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-cds-border-subtle">
          <h2 class="text-sm font-bold uppercase tracking-wider text-cds-text-helper">
            Gisements disponibles ({{ listings.length }})
          </h2>
          <span class="text-xs font-medium text-cds-link-primary">Classés par proximité</span>
        </div>

        <div v-if="loading" class="py-12 flex justify-center">
          <span class="eco-spinner w-8 h-8"></span>
        </div>

        <div v-else-if="listings.length === 0" class="p-8 bg-cds-layer-01 border border-cds-border-subtle text-center">
          <p class="text-sm text-cds-text-helper">Aucun gisement trouvé dans ce rayon.</p>
          <p class="text-xs text-cds-text-helper mt-1">Élargissez le rayon de recherche ou changez de matière.</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="item in listings"
            :key="item.id"
            :id="`listing-card-${item.id}`"
            class="p-4 bg-cds-layer-01 border transition cursor-pointer"
            :class="selectedListingId === item.id
              ? 'border-cds-border-interactive bg-cds-layer-hover-01'
              : 'border-cds-border-subtle hover:border-cds-border-interactive'"
            @click="selectedListingId = item.id"
          >
            <div class="flex gap-4">
              <!-- Vignette -->
              <div class="w-20 h-20 bg-cds-background border border-cds-border-subtle overflow-hidden shrink-0">
                <img
                  v-if="item.thumbnail_url"
                  :src="item.thumbnail_url"
                  :alt="item.title"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-cds-text-helper text-[10px]">
                  Pas d'image
                </div>
              </div>

              <!-- Détails -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between">
                  <h3 class="text-sm font-bold text-cds-text-primary truncate pr-2">{{ item.title }}</h3>
                  <span class="text-[11px] font-mono px-2 py-0.5 bg-cds-layer-02 border border-cds-border-subtle text-cds-link-primary shrink-0">
                    {{ formatNumber(item.distance_km, 1) }} km
                  </span>
                </div>

                <div class="flex items-center space-x-2 mt-1">
                  <span class="text-xs font-semibold text-cds-text-secondary">
                    {{ formatQuantity(item.estimated_quantity, item.unit) }}
                  </span>
                  <span class="text-[10px] text-cds-text-helper bg-cds-background px-2 py-0.5 border border-cds-border-subtle">
                    {{ item.category_name }}
                  </span>
                </div>

                <p class="text-xs text-cds-text-helper truncate mt-1">📍 {{ item.address_text }}</p>

                <div class="mt-3 flex items-center justify-between">
                  <div class="text-xs font-bold" :class="item.is_free_donation ? 'text-cds-support-warning' : 'text-cds-link-primary'">
                    {{ item.is_free_donation ? 'Don gratuit' : `${formatMoney(item.price_per_unit)} / ${item.unit}` }}
                  </div>

                  <button
                    v-if="user?.role === 'collector'"
                    @click.stop="openReserveModal(item)"
                    type="button"
                    class="cds--btn cds--btn--primary cds--btn--sm"
                  >
                    Réserver
                  </button>
                  <NuxtLink
                    v-else
                    :to="`/marketplace`"
                    class="text-xs text-cds-text-helper hover:text-cds-text-primary"
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

    <!-- Modale de réservation (collecteurs) -->
    <div
      v-if="reservingListing"
      class="cds--modal cds--modal--enable-presence"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titre-modale-reservation"
    >
      <div class="cds--modal-container cds--modal-container--sm">
        <header class="cds--modal-header">
          <h2 id="titre-modale-reservation" class="cds--modal-header__heading">
            Confirmer la réservation & séquestre
          </h2>
          <button
            class="cds--modal-close"
            type="button"
            aria-label="Fermer"
            @click="reservingListing = null"
          >
            <Lineicons
              class="cds--modal-close__icon"
              :icon="Icons.close"
              :size="20"
              color="currentColor"
            />
          </button>
        </header>

        <div class="cds--modal-content">
          <p class="text-xs text-cds-text-helper">
            Gisement : <b class="text-cds-text-secondary">{{ reservingListing.title }}</b>
          </p>

          <div class="mt-4 p-4 bg-cds-background border border-cds-border-subtle space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-cds-text-helper">Quantité disponible :</span>
              <span class="font-semibold text-cds-text-primary">
                {{ formatQuantity(reservingListing.estimated_quantity, reservingListing.unit) }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-cds-text-helper">Prix unitaire :</span>
              <span class="font-semibold text-cds-text-primary">
                {{ reservingListing.is_free_donation ? '0 (Don)' : formatMoney(reservingListing.price_per_unit) }}
              </span>
            </div>
            <div class="flex justify-between border-t border-cds-border-subtle pt-2 font-bold">
              <span class="text-cds-link-primary">Montant total séquestré :</span>
              <span class="text-cds-link-primary">
                {{ formatMoney((toNumber(reservingListing.estimated_quantity) ?? 0) * (reservingListing.is_free_donation ? 0 : (toNumber(reservingListing.price_per_unit) ?? 0))) }}
              </span>
            </div>
          </div>
        </div>

        <footer class="cds--modal-footer">
          <button
            class="cds--btn cds--btn--secondary"
            type="button"
            @click="reservingListing = null"
          >
            Annuler
          </button>
          <button
            class="cds--btn cds--btn--primary"
            type="button"
            :disabled="actionLoading"
            @click="confirmReservation"
          >
            {{ actionLoading ? 'Verrouillage séquestre...' : 'Confirmer séquestre' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { NearbyListing, WasteCategory } from '~/types'

const { user } = useAuth()
const { apiFetch } = useApi()
// Les champs NUMERIC de l'API arrivent en chaîne : tout affichage numérique
// (montants, quantités) passe par useFormat(), jamais par de l'arithmétique brute.
const { formatMoney, formatNumber, formatQuantity, toNumber } = useFormat()

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
