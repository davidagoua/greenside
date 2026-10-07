<template>
  <div>
    <AdminNav />

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Catégories de matières</h1>
          <p class="text-xs text-cds-text-helper mt-1">
            Référentiel utilisé par les annonces : facteurs d'évitement CO₂ et prix indicatifs
          </p>
        </div>
        <div class="flex items-center gap-2 self-start">
          <button
            type="button"
            :disabled="loading"
            class="cds--btn cds--btn--secondary cds--btn--sm"
            @click="fetchCategories"
          >
            <Lineicons :icon="Icons.loading" :size="16" color="currentColor" />
            <span class="ml-2">{{ loading ? 'Chargement…' : 'Rafraîchir' }}</span>
          </button>
          <button
            type="button"
            class="cds--btn cds--btn--primary cds--btn--sm"
            @click="openCreateForm"
          >
            <Lineicons :icon="Icons.add" :size="16" color="currentColor" />
            <span class="ml-2">Nouvelle catégorie</span>
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error text-cds-support-error text-xs flex items-start justify-between gap-4"
      >
        <span class="flex items-start gap-2">
          <Lineicons :icon="Icons.error" :size="16" color="currentColor" class="shrink-0 mt-0.5" />
          <span>{{ error }}</span>
        </span>
        <button type="button" class="hover:underline shrink-0 font-medium" @click="fetchCategories">Réessayer</button>
      </div>

      <div
        v-if="successMessage"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-success text-cds-text-primary text-xs flex items-start justify-between gap-4"
      >
        <span class="flex items-start gap-2">
          <Lineicons :icon="Icons.success" :size="16" color="var(--cds-support-success)" class="shrink-0 mt-0.5" />
          <span>{{ successMessage }}</span>
        </span>
        <button type="button" class="text-cds-support-success hover:underline shrink-0 font-medium" @click="successMessage = ''">Fermer</button>
      </div>

      <!-- Formulaire de création -->
      <form
        v-if="showCreateForm"
        class="p-6 bg-cds-layer-01 border border-cds-border-interactive space-y-4"
        @submit.prevent="submitCreate"
      >
        <h2 class="text-sm font-bold text-cds-text-primary">Créer une catégorie de matière</h2>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div class="cds--form-item">
            <label class="cds--label" for="create-slug">Slug *</label>
            <input
              id="create-slug"
              v-model="createForm.slug"
              type="text"
              required
              pattern="[a-z0-9-]+"
              placeholder="ex. pet-bouteilles"
              class="cds--text-input font-mono"
            />
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="create-name">Nom affiché *</label>
            <input
              id="create-name"
              v-model="createForm.name"
              type="text"
              required
              minlength="2"
              maxlength="100"
              placeholder="ex. Plastique PET"
              class="cds--text-input"
            />
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="create-unit">Unité *</label>
            <div class="cds--select">
              <div class="cds--select-input__wrapper">
                <select id="create-unit" v-model="createForm.unit" class="cds--select-input">
                  <option value="kg">kg</option>
                  <option value="tonne">tonne</option>
                  <option value="litre">litre</option>
                </select>
                <Lineicons class="cds--select__arrow" :icon="Icons.expand" :size="16" color="var(--cds-icon-primary)" />
              </div>
            </div>
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="create-co2">Facteur CO₂ / unité *</label>
            <input
              id="create-co2"
              v-model.number="createForm.co2_factor_per_unit"
              type="number"
              required
              min="0"
              step="0.0001"
              class="cds--text-input font-mono"
            />
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="create-price">Prix suggéré (FCFA)</label>
            <input
              id="create-price"
              v-model.number="createForm.suggested_price_per_unit"
              type="number"
              min="0"
              step="0.01"
              class="cds--text-input font-mono"
            />
          </div>
        </div>

        <p class="text-[10px] text-cds-text-helper">
          Le slug sert d'identifiant technique (minuscules, chiffres et tirets uniquement) et ne peut
          plus être modifié après création. Le facteur CO₂ est exprimé en kg CO₂e évités par unité recyclée.
        </p>

        <p v-if="formError" class="p-3 bg-cds-layer-02 border-l-2 border-cds-support-error text-cds-support-error text-xs">
          {{ formError }}
        </p>

        <div class="flex gap-3">
          <button
            type="button"
            :disabled="saving"
            class="cds--btn cds--btn--secondary"
            @click="showCreateForm = false"
          >
            Annuler
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="cds--btn cds--btn--primary"
          >
            {{ saving ? 'Création…' : 'Créer la catégorie' }}
          </button>
        </div>
      </form>

      <div v-if="loading && !categories.length" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-14 bg-cds-skeleton-background border border-cds-border-subtle animate-pulse"></div>
      </div>

      <!-- Tableau -->
      <div v-else class="bg-cds-layer-01 border border-cds-border-subtle">
        <div class="cds--data-table-content">
          <table class="cds--data-table">
            <thead>
              <tr>
                <th scope="col">Matière</th>
                <th scope="col">Slug</th>
                <th scope="col">Unité</th>
                <th scope="col">Facteur CO₂</th>
                <th scope="col">Prix suggéré</th>
                <th scope="col" align="right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="cat in categories" :key="cat.id">
                <!-- Ligne en lecture -->
                <tr v-if="editingId !== cat.id" class="hover:bg-cds-layer-hover-01 transition-colors">
                  <td class="py-3 px-4">
                    <span class="flex items-center gap-2">
                      <span class="w-2.5 h-2.5 rounded-full bg-cds-support-success"></span>
                      <span class="font-bold text-cds-text-primary">{{ cat.name }}</span>
                    </span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="font-mono text-cds-text-helper">{{ cat.slug }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-cds-text-secondary">{{ cat.unit }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="font-mono text-cds-link-primary">
                      {{ formatNumber(cat.co2_factor_per_unit, 4) }} kg CO₂e / {{ cat.unit }}
                    </span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="font-mono text-cds-support-warning">
                      {{ formatMoney(cat.suggested_price_per_unit) }}
                    </span>
                  </td>
                  <td class="py-3 px-4 !text-right whitespace-nowrap" align="right">
                    <button
                      type="button"
                      class="cds--btn cds--btn--secondary cds--btn--sm"
                      @click="startEdit(cat)"
                    >
                      <Lineicons :icon="Icons.edit" :size="16" color="currentColor" />
                      <span class="ml-2">Modifier</span>
                    </button>
                    <button
                      type="button"
                      class="cds--btn cds--btn--danger--ghost cds--btn--sm ml-2"
                      @click="askDelete(cat)"
                    >
                      <Lineicons :icon="Icons.delete" :size="16" color="currentColor" />
                      <span class="ml-2">Supprimer</span>
                    </button>
                  </td>
                </tr>

                <!-- Ligne en édition -->
                <tr v-else class="bg-cds-layer-02">
                  <td class="py-3 px-4">
                    <input
                      v-model="editForm.name"
                      type="text"
                      minlength="2"
                      maxlength="100"
                      aria-label="Nom affiché"
                      class="cds--text-input w-full"
                    />
                  </td>
                  <td class="py-3 px-4">
                    <span class="font-mono text-cds-text-helper">{{ cat.slug }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <div class="cds--select">
                      <div class="cds--select-input__wrapper">
                        <select v-model="editForm.unit" aria-label="Unité" class="cds--select-input">
                          <option value="kg">kg</option>
                          <option value="tonne">tonne</option>
                          <option value="litre">litre</option>
                        </select>
                        <Lineicons class="cds--select__arrow" :icon="Icons.expand" :size="16" color="var(--cds-icon-primary)" />
                      </div>
                    </div>
                  </td>
                  <td class="py-3 px-4">
                    <input
                      v-model.number="editForm.co2_factor_per_unit"
                      type="number"
                      min="0"
                      step="0.0001"
                      aria-label="Facteur CO₂ par unité"
                      class="cds--text-input w-28 font-mono"
                    />
                  </td>
                  <td class="py-3 px-4">
                    <input
                      v-model.number="editForm.suggested_price_per_unit"
                      type="number"
                      min="0"
                      step="0.01"
                      aria-label="Prix suggéré par unité"
                      class="cds--text-input w-28 font-mono"
                    />
                  </td>
                  <td class="py-3 px-4 !text-right whitespace-nowrap" align="right">
                    <button
                      type="button"
                      :disabled="saving"
                      class="cds--btn cds--btn--primary cds--btn--sm"
                      @click="submitEdit(cat)"
                    >
                      <Lineicons :icon="Icons.check" :size="16" color="currentColor" />
                      <span class="ml-2">{{ saving ? '…' : 'Enregistrer' }}</span>
                    </button>
                    <button
                      type="button"
                      :disabled="saving"
                      class="cds--btn cds--btn--secondary cds--btn--sm ml-2"
                      @click="cancelEdit"
                    >
                      Annuler
                    </button>
                  </td>
                </tr>
              </template>

              <tr v-if="!categories.length">
                <td colspan="6" class="py-12 !text-center">
                  <span class="text-cds-text-helper">Aucune catégorie enregistrée.</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="editingId && formError" class="px-4 py-3 border-t border-cds-border-subtle bg-cds-layer-02 text-cds-support-error text-xs">
          {{ formError }}
        </p>
      </div>
    </div>

    <!-- Confirmation de suppression -->
    <div
      v-if="pendingDelete"
      class="cds--modal cds--modal--enable-presence"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="delete-category-title"
      @click.self="pendingDelete = null"
    >
      <div class="cds--modal-container">
        <header class="cds--modal-header">
          <h2 id="delete-category-title" class="cds--modal-header__heading">Supprimer cette catégorie ?</h2>
          <button
            class="cds--modal-close"
            type="button"
            aria-label="Fermer"
            @click="pendingDelete = null"
          >
            <Lineicons class="cds--modal-close__icon" :icon="Icons.close" :size="20" color="currentColor" />
          </button>
        </header>

        <div class="cds--modal-content">
          <p class="text-xs text-cds-text-secondary">
            <b class="text-cds-text-primary">{{ pendingDelete.name }}</b> ({{ pendingDelete.slug }}) ne sera plus
            proposée lors du dépôt d'annonce. La suppression est refusée si des annonces y sont déjà rattachées.
          </p>

          <p v-if="modalError" class="mt-4 p-3 bg-cds-layer-02 border-l-2 border-cds-support-error text-cds-support-error text-xs">
            {{ modalError }}
          </p>
        </div>

        <footer class="cds--modal-footer">
          <button
            type="button"
            :disabled="saving"
            class="cds--btn cds--btn--secondary"
            @click="pendingDelete = null"
          >
            Annuler
          </button>
          <button
            type="button"
            :disabled="saving"
            class="cds--btn cds--btn--danger"
            @click="confirmDelete"
          >
            {{ saving ? 'Suppression…' : 'Supprimer' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { WasteCategory, CategoryInput, CategoryUpdate } from '~/types'

definePageMeta({ middleware: 'admin' })

useHead({ title: 'Catégories — Administration EcoLoop' })

const { apiFetch } = useApi()
const { formatNumber, formatMoney, toNumber, errorMessage } = useFormat()

const categories = ref<WasteCategory[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const formError = ref('')
const modalError = ref('')
const successMessage = ref('')

const showCreateForm = ref(false)
const createForm = reactive<CategoryInput>({
  slug: '',
  name: '',
  unit: 'kg',
  co2_factor_per_unit: 0,
  suggested_price_per_unit: 0
})

const editingId = ref<string | null>(null)
const editForm = reactive({
  name: '',
  unit: 'kg' as CategoryInput['unit'],
  co2_factor_per_unit: 0,
  suggested_price_per_unit: 0
})

const pendingDelete = ref<WasteCategory | null>(null)

const fetchCategories = async () => {
  loading.value = true
  error.value = ''
  try {
    categories.value = await apiFetch<WasteCategory[]>('/categories')
  } catch (err) {
    categories.value = []
    error.value = errorMessage(err, 'Impossible de charger les catégories')
  } finally {
    loading.value = false
  }
}

const openCreateForm = () => {
  showCreateForm.value = true
  formError.value = ''
  createForm.slug = ''
  createForm.name = ''
  createForm.unit = 'kg'
  createForm.co2_factor_per_unit = 0
  createForm.suggested_price_per_unit = 0
}

const submitCreate = async () => {
  formError.value = ''

  const slug = createForm.slug.trim().toLowerCase()
  if (!/^[a-z0-9-]{2,50}$/.test(slug)) {
    formError.value = 'Le slug doit contenir entre 2 et 50 caractères : minuscules, chiffres et tirets uniquement.'
    return
  }
  if (createForm.name.trim().length < 2) {
    formError.value = 'Le nom affiché doit contenir au moins 2 caractères.'
    return
  }
  if (createForm.co2_factor_per_unit < 0) {
    formError.value = 'Le facteur CO₂ ne peut pas être négatif.'
    return
  }

  saving.value = true
  try {
    await apiFetch<WasteCategory>('/categories', {
      method: 'POST',
      body: {
        slug,
        name: createForm.name.trim(),
        unit: createForm.unit,
        co2_factor_per_unit: createForm.co2_factor_per_unit,
        suggested_price_per_unit: createForm.suggested_price_per_unit
      }
    })
    successMessage.value = `Catégorie « ${createForm.name.trim()} » créée.`
    showCreateForm.value = false
    await fetchCategories()
  } catch (err) {
    formError.value = errorMessage(err, 'Échec de la création de la catégorie')
  } finally {
    saving.value = false
  }
}

const startEdit = (cat: WasteCategory) => {
  editingId.value = cat.id
  formError.value = ''
  editForm.name = cat.name
  editForm.unit = (cat.unit as CategoryInput['unit']) || 'kg'
  editForm.co2_factor_per_unit = toNumber(cat.co2_factor_per_unit) ?? 0
  editForm.suggested_price_per_unit = toNumber(cat.suggested_price_per_unit) ?? 0
}

const cancelEdit = () => {
  editingId.value = null
  formError.value = ''
}

const submitEdit = async (cat: WasteCategory) => {
  formError.value = ''

  if (editForm.name.trim().length < 2) {
    formError.value = 'Le nom affiché doit contenir au moins 2 caractères.'
    return
  }
  if (editForm.co2_factor_per_unit < 0) {
    formError.value = 'Le facteur CO₂ ne peut pas être négatif.'
    return
  }

  const payload: CategoryUpdate = {
    name: editForm.name.trim(),
    unit: editForm.unit,
    co2_factor_per_unit: editForm.co2_factor_per_unit,
    suggested_price_per_unit: editForm.suggested_price_per_unit
  }

  saving.value = true
  try {
    const updated = await apiFetch<WasteCategory>(`/categories/${cat.id}`, {
      method: 'PATCH',
      body: payload
    })
    const index = categories.value.findIndex((c) => c.id === cat.id)
    if (index !== -1) categories.value[index] = { ...categories.value[index], ...updated }
    successMessage.value = `Catégorie « ${updated.name} » mise à jour.`
    editingId.value = null
  } catch (err) {
    formError.value = errorMessage(err, 'Échec de la mise à jour')
  } finally {
    saving.value = false
  }
}

const askDelete = (cat: WasteCategory) => {
  modalError.value = ''
  pendingDelete.value = cat
}

const confirmDelete = async () => {
  if (!pendingDelete.value) return
  const target = pendingDelete.value
  saving.value = true
  modalError.value = ''
  try {
    await apiFetch(`/categories/${target.id}`, { method: 'DELETE' })
    categories.value = categories.value.filter((c) => c.id !== target.id)
    successMessage.value = `Catégorie « ${target.name} » supprimée.`
    pendingDelete.value = null
  } catch (err) {
    modalError.value = errorMessage(err, 'Échec de la suppression')
  } finally {
    saving.value = false
  }
}

onMounted(fetchCategories)
</script>
