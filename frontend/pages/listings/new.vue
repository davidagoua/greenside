<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Déposer un gisement de déchets</h1>
        <p class="text-xs text-cds-text-helper mt-1">
          Renseignez les détails du gisement pour les collecteurs agréés de votre région
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Title & Category -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2 cds--form-item">
            <label class="cds--label" for="listing-title">Titre de l'annonce</label>
            <input
              id="listing-title"
              v-model="form.title"
              type="text"
              required
              placeholder="Ex: 500 kg de plastique PET en balles compactées"
              class="cds--text-input"
            />
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="listing-category">Catégorie de matière</label>
            <div class="cds--select">
              <div class="cds--select-input__wrapper">
                <select
                  id="listing-category"
                  v-model="form.category_id"
                  required
                  class="cds--select-input"
                >
                  <option value="" disabled>Sélectionnez une catégorie</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }} ({{ cat.unit }})
                  </option>
                </select>
                <Lineicons class="cds--select__arrow" :icon="Icons.expand" :size="16" color="var(--cds-icon-primary)" />
              </div>
            </div>
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="listing-quantity">
              Quantité estimée ({{ selectedCategoryUnit }})
            </label>
            <input
              id="listing-quantity"
              v-model.number="form.estimated_quantity"
              type="number"
              step="0.01"
              min="0.1"
              required
              placeholder="500"
              class="cds--text-input"
            />
          </div>
        </div>

        <!-- Pricing & Donation -->
        <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
          <div class="flex items-center justify-between gap-3 mb-3">
            <label class="cds--label">Type de cession</label>
            <!-- Le don gratuit est une information « avertissement » : jeton support-warning -->
            <div class="cds--checkbox-wrapper">
              <input
                id="listing-free-donation"
                type="checkbox"
                class="cds--checkbox"
                v-model="form.is_free_donation"
              />
              <label for="listing-free-donation" class="cds--checkbox-label text-cds-support-warning">
                Don gratuit contre enlèvement
              </label>
            </div>
          </div>

          <div v-if="!form.is_free_donation" class="cds--form-item">
            <label class="cds--label" for="listing-price">
              Prix unitaire demandé (en FCFA / {{ selectedCategoryUnit }})
            </label>
            <input
              id="listing-price"
              v-model.number="form.price_per_unit"
              type="number"
              step="0.01"
              min="0"
              required
              class="cds--text-input"
            />
          </div>
        </div>

        <!-- Location & Geocoding -->
        <div class="space-y-3">
          <div class="cds--form-item">
            <label class="cds--label" for="listing-address-query">Localisation du gisement</label>
            <div class="flex gap-2">
              <input
                id="listing-address-query"
                v-model="searchAddressQuery"
                type="text"
                placeholder="Rechercher une adresse / ville pour géocoder..."
                class="cds--text-input"
              />
              <button
                @click="searchAddress"
                type="button"
                :disabled="geocoding"
                class="cds--btn cds--btn--secondary shrink-0"
              >
                {{ geocoding ? 'Recherche...' : 'Géocoder' }}
              </button>
            </div>
          </div>

          <!-- Geocoding suggestions dropdown -->
          <div v-if="addressSuggestions.length > 0" class="p-2 bg-cds-layer-02 border border-cds-border-subtle space-y-1">
            <div
              v-for="(sug, idx) in addressSuggestions"
              :key="idx"
              @click="selectAddress(sug)"
              class="p-2 hover:bg-cds-layer-hover-01 text-xs text-cds-text-secondary cursor-pointer flex justify-between items-center"
            >
              <span class="truncate pr-2">{{ sug.display_name }}</span>
              <span class="text-[10px] text-cds-link-primary shrink-0 font-mono">{{ sug.lat.toFixed(3) }}, {{ sug.lng.toFixed(3) }}</span>
            </div>
          </div>

          <!-- Selected Location Details -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-cds-layer-02 border border-cds-border-subtle">
            <div>
              <span class="text-[11px] text-cds-text-helper block">Adresse retenue :</span>
              <span class="text-xs text-cds-text-secondary font-medium">{{ form.location.address_text || 'Aucune adresse sélectionnée' }}</span>
            </div>
            <div>
              <span class="text-[11px] text-cds-text-helper block">Coordonnées GPS :</span>
              <span class="text-xs text-cds-link-primary font-mono">{{ form.location.lat }}, {{ form.location.lng }}</span>
            </div>
          </div>
        </div>

        <!-- Photos Upload via Media Service -->
        <div class="cds--form-item">
          <label class="cds--label" for="listing-photo">Photos du gisement (max 5 MB - JPEG/PNG/WEBP)</label>
          <div class="flex items-center gap-3">
            <input
              id="listing-photo"
              type="file"
              ref="fileInputRef"
              accept="image/jpeg,image/png,image/webp"
              @change="handleFileUpload"
              class="hidden"
            />
            <button
              @click="fileInputRef?.click()"
              type="button"
              :disabled="uploadingImage"
              class="cds--btn cds--btn--secondary"
            >
              <Lineicons :icon="Icons.upload" :size="16" color="currentColor" />
              <span class="ml-2">{{ uploadingImage ? 'Upload en cours...' : 'Ajouter une photo' }}</span>
            </button>
          </div>

          <!-- Uploaded images preview -->
          <div v-if="form.images_urls.length > 0" class="mt-3 flex flex-wrap gap-3">
            <div
              v-for="(url, idx) in form.images_urls"
              :key="idx"
              class="relative w-20 h-20 overflow-hidden border border-cds-border-subtle"
            >
              <img :src="url" class="w-full h-full object-cover" />
              <button
                @click="form.images_urls.splice(idx, 1)"
                type="button"
                aria-label="Retirer cette photo"
                title="Retirer cette photo"
                class="absolute top-0 right-0 p-1 bg-cds-danger text-cds-text-on-color"
              >
                <Lineicons :icon="Icons.close" :size="14" color="currentColor" />
              </button>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="cds--form-item">
          <label class="cds--label" for="listing-description">Description & Conditionnement</label>
          <textarea
            id="listing-description"
            v-model="form.description"
            rows="3"
            placeholder="Ex: Matière propre, stockée sous abri, disponible sur palettes."
            class="cds--text-area"
          ></textarea>
        </div>

        <button
          type="submit"
          :disabled="submitting"
          class="cds--btn cds--btn--primary cds--btn--full justify-center"
        >
          <span class="flex items-center justify-center">
            <span v-if="submitting" class="eco-spinner w-4 h-4 mr-2"></span>
            <span>Publier le gisement</span>
          </span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { WasteCategory } from '~/types'

const { apiFetch } = useApi()
const categories = ref<WasteCategory[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

const searchAddressQuery = ref('')
const addressSuggestions = ref<any[]>([])
const geocoding = ref(false)
const uploadingImage = ref(false)
const submitting = ref(false)

const form = reactive({
  title: '',
  category_id: '',
  estimated_quantity: 100,
  price_per_unit: 0,
  is_free_donation: false,
  description: '',
  images_urls: [] as string[],
  location: {
    address_text: 'Dakar, Sénégal',
    lat: 14.7167,
    lng: -17.4677,
    label: 'Dépôt principal'
  }
})

const selectedCategoryUnit = computed(() => {
  const cat = categories.value.find(c => c.id === form.category_id)
  return cat ? cat.unit : 'kg'
})

const searchAddress = async () => {
  if (!searchAddressQuery.value || searchAddressQuery.value.length < 3) return
  geocoding.value = true
  try {
    addressSuggestions.value = await apiFetch<any[]>('/geocode', {
      params: { q: searchAddressQuery.value }
    })
  } catch (err) {
    console.error('Erreur géocodage:', err)
  } finally {
    geocoding.value = false
  }
}

const selectAddress = (sug: any) => {
  form.location.address_text = sug.display_name
  form.location.lat = parseFloat(sug.lat.toFixed(5))
  form.location.lng = parseFloat(sug.lng.toFixed(5))
  addressSuggestions.value = []
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadingImage.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', 'listings')

    const res = await apiFetch<any>('/media/upload', {
      method: 'POST',
      body: formData
    })
    form.images_urls.push(res.url)
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || "Erreur lors de l'upload")
  } finally {
    uploadingImage.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      category_id: form.category_id,
      estimated_quantity: form.estimated_quantity,
      price_per_unit: form.is_free_donation ? 0 : form.price_per_unit,
      is_free_donation: form.is_free_donation,
      description: form.description || null,
      images_urls: form.images_urls,
      location: form.location
    }

    await apiFetch('/listings', {
      method: 'POST',
      body: payload
    })

    navigateTo('/marketplace')
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur lors de la création')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    categories.value = await apiFetch<WasteCategory[]>('/categories')
    if (categories.value.length > 0) {
      form.category_id = categories.value[0].id
    }
  } catch (err) {
    console.error('Erreur chargement catégories:', err)
  }
})
</script>
