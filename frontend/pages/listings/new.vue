<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-white tracking-tight">Déposer un gisement de déchets</h1>
        <p class="text-xs text-slate-400 mt-1">
          Renseignez les détails du gisement pour les collecteurs agréés de votre région
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Title & Category -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Titre de l'annonce</label>
            <input
              v-model="form.title"
              type="text"
              required
              placeholder="Ex: 500 kg de plastique PET en balles compactées"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-eco-500 transition"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Catégorie de matière</label>
            <select
              v-model="form.category_id"
              required
              class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-eco-500 transition"
            >
              <option value="" disabled>Sélectionnez une catégorie</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }} ({{ cat.unit }})
              </option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">
              Quantité estimée ({{ selectedCategoryUnit }})
            </label>
            <input
              v-model.number="form.estimated_quantity"
              type="number"
              step="0.01"
              min="0.1"
              required
              placeholder="500"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-eco-500 transition"
            />
          </div>
        </div>

        <!-- Pricing & Donation -->
        <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800">
          <div class="flex items-center justify-between mb-3">
            <label class="text-xs font-semibold text-slate-300">Type de cession</label>
            <label class="flex items-center space-x-2 cursor-pointer">
              <input type="checkbox" v-model="form.is_free_donation" class="rounded bg-slate-900 border-slate-700 text-eco-500 focus:ring-0" />
              <span class="text-xs text-amber-400 font-medium">Don gratuit contre enlèvement</span>
            </label>
          </div>

          <div v-if="!form.is_free_donation">
            <label class="block text-xs text-slate-400 mb-1">
              Prix unitaire demandé (en FCFA / {{ selectedCategoryUnit }})
            </label>
            <input
              v-model.number="form.price_per_unit"
              type="number"
              step="0.01"
              min="0"
              required
              class="w-full px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-eco-500"
            />
          </div>
        </div>

        <!-- Location & Geocoding -->
        <div class="space-y-3">
          <label class="block text-xs font-semibold text-slate-300">Localisation du gisement</label>
          <div class="flex space-x-2">
            <input
              v-model="searchAddressQuery"
              type="text"
              placeholder="Rechercher une adresse / ville pour géocoder..."
              class="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-eco-500"
            />
            <button
              @click="searchAddress"
              type="button"
              :disabled="geocoding"
              class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
            >
              {{ geocoding ? 'Recherche...' : 'Géocoder' }}
            </button>
          </div>

          <!-- Geocoding suggestions dropdown -->
          <div v-if="addressSuggestions.length > 0" class="p-2 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <div
              v-for="(sug, idx) in addressSuggestions"
              :key="idx"
              @click="selectAddress(sug)"
              class="p-2 rounded-lg hover:bg-slate-900 text-xs text-slate-300 cursor-pointer flex justify-between items-center"
            >
              <span class="truncate pr-2">{{ sug.display_name }}</span>
              <span class="text-[10px] text-eco-400 shrink-0 font-mono">{{ sug.lat.toFixed(3) }}, {{ sug.lng.toFixed(3) }}</span>
            </div>
          </div>

          <!-- Selected Location Details -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div>
              <span class="text-[11px] text-slate-400 block">Adresse retenue :</span>
              <span class="text-xs text-slate-200 font-medium">{{ form.location.address_text || 'Aucune adresse sélectionnée' }}</span>
            </div>
            <div>
              <span class="text-[11px] text-slate-400 block">Coordonnées GPS :</span>
              <span class="text-xs text-eco-400 font-mono">{{ form.location.lat }}, {{ form.location.lng }}</span>
            </div>
          </div>
        </div>

        <!-- Photos Upload via Media Service -->
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Photos du gisement (max 5 MB - JPEG/PNG/WEBP)</label>
          <div class="flex items-center space-x-3">
            <input
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
              class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center space-x-2"
            >
              <svg class="w-4 h-4 text-eco-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{{ uploadingImage ? 'Upload en cours...' : 'Ajouter une photo' }}</span>
            </button>
          </div>

          <!-- Uploaded images preview -->
          <div v-if="form.images_urls.length > 0" class="mt-3 flex flex-wrap gap-3">
            <div
              v-for="(url, idx) in form.images_urls"
              :key="idx"
              class="relative w-20 h-20 rounded-xl overflow-hidden border border-slate-800"
            >
              <img :src="url" class="w-full h-full object-cover" />
              <button
                @click="form.images_urls.splice(idx, 1)"
                type="button"
                class="absolute top-1 right-1 p-1 bg-red-600/80 hover:bg-red-600 text-white rounded-full text-[10px]"
              >
                ✕
              </button>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Description & Conditionnement</label>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="Ex: Matière propre, stockée sous abri, disponible sur palettes."
            class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-eco-500 transition"
          ></textarea>
        </div>

        <button
          type="submit"
          :disabled="submitting"
          class="w-full py-3.5 px-4 rounded-xl font-bold text-white bg-eco-600 hover:bg-eco-500 shadow-lg shadow-eco-600/30 transition disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <span v-if="submitting" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <span>Publier le gisement</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
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
