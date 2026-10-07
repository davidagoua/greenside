<template>
  <div>
    <AdminNav />

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Utilisateurs</h1>
          <p class="text-xs text-cds-text-helper mt-1">
            Producteurs, collecteurs et administrateurs de la plateforme
          </p>
        </div>
        <button
          type="button"
          :disabled="loading"
          class="cds--btn cds--btn--secondary cds--btn--sm self-start"
          @click="fetchUsers"
        >
          <Lineicons :icon="Icons.loading" :size="16" color="currentColor" />
          <span class="ml-2">{{ loading ? 'Chargement…' : 'Rafraîchir' }}</span>
        </button>
      </div>

      <div
        v-if="error"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error text-cds-support-error text-xs flex items-start justify-between gap-4"
      >
        <span class="flex items-start gap-2">
          <Lineicons :icon="Icons.error" :size="16" color="currentColor" class="shrink-0 mt-0.5" />
          <span>{{ error }}</span>
        </span>
        <button type="button" class="hover:underline shrink-0 font-medium" @click="fetchUsers">Réessayer</button>
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

      <!-- Filtres -->
      <div class="p-4 bg-cds-layer-01 border border-cds-border-subtle grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="cds--form-item sm:col-span-2">
          <label class="cds--label" for="users-search">Recherche</label>
          <input
            id="users-search"
            v-model="search"
            type="search"
            placeholder="Email ou organisation…"
            class="cds--text-input"
          />
        </div>

        <div class="cds--form-item">
          <label class="cds--label" for="users-role">Rôle</label>
          <div class="cds--select">
            <div class="cds--select-input__wrapper">
              <select id="users-role" v-model="roleFilter" class="cds--select-input">
                <option value="">Tous les rôles</option>
                <option value="producer">Producteurs</option>
                <option value="collector">Collecteurs</option>
                <option value="admin">Administrateurs</option>
              </select>
              <Lineicons class="cds--select__arrow" :icon="Icons.expand" :size="16" color="var(--cds-icon-primary)" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading && !users.length" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-14 bg-cds-skeleton-background border border-cds-border-subtle animate-pulse"></div>
      </div>

      <!-- Tableau -->
      <div v-else class="bg-cds-layer-01 border border-cds-border-subtle">
        <div class="cds--data-table-content">
          <table class="cds--data-table">
            <thead>
              <tr>
                <th scope="col">Utilisateur</th>
                <th scope="col">Rôle</th>
                <th scope="col">Téléphone</th>
                <th scope="col">Statut</th>
                <th scope="col">Inscrit le</th>
                <th scope="col" align="right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" class="hover:bg-cds-layer-hover-01 transition-colors">
                <td class="py-3 px-4">
                  <span class="block font-semibold text-cds-text-primary max-w-[18rem] truncate" :title="u.email">
                    {{ u.email }}
                  </span>
                  <span class="block text-[10px] text-cds-text-helper max-w-[18rem] truncate">
                    {{ u.organization_name || 'Sans organisation' }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span class="cds--tag" :class="roleBadgeClass(u.role)">
                    {{ roleLabel(u.role) }}
                  </span>
                </td>
                <td class="py-3 px-4 whitespace-nowrap">
                  <span class="font-mono text-cds-text-secondary">{{ u.phone }}</span>
                </td>
                <td class="py-3 px-4">
                  <span class="cds--tag" :class="u.is_active ? 'cds--tag--green' : 'cds--tag--red'">
                    {{ u.is_active ? 'Actif' : 'Désactivé' }}
                  </span>
                </td>
                <td class="py-3 px-4 whitespace-nowrap">
                  <span class="text-cds-text-helper">{{ formatDate(u.created_at) }}</span>
                </td>
                <td class="py-3 px-4 !text-right" align="right">
                  <span v-if="u.id === currentUserId" class="text-[11px] text-cds-text-helper italic">
                    Votre compte
                  </span>
                  <button
                    v-else-if="u.is_active"
                    type="button"
                    :disabled="togglingId === u.id"
                    class="cds--btn cds--btn--danger--ghost cds--btn--sm"
                    @click="askDeactivate(u)"
                  >
                    <Lineicons :icon="Icons.lock" :size="16" color="currentColor" />
                    <span class="ml-2">Désactiver</span>
                  </button>
                  <button
                    v-else
                    type="button"
                    :disabled="togglingId === u.id"
                    class="cds--btn cds--btn--primary cds--btn--sm"
                    @click="setActive(u, true)"
                  >
                    <Lineicons :icon="Icons.success" :size="16" color="currentColor" />
                    <span class="ml-2">{{ togglingId === u.id ? '…' : 'Réactiver' }}</span>
                  </button>
                </td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="6" class="py-12 !text-center">
                  <span class="text-cds-text-helper">Aucun utilisateur ne correspond à ces critères.</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-4 py-3 border-t border-cds-border-subtle flex items-center justify-between gap-4">
          <span class="text-[10px] text-cds-text-helper">
            {{ users.length }} résultat{{ users.length > 1 ? 's' : '' }} · page {{ page }}
          </span>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="page === 1 || loading"
              class="cds--btn cds--btn--tertiary cds--btn--sm"
              @click="previousPage"
            >
              <Lineicons :icon="Icons.previous" :size="16" color="currentColor" />
              <span class="ml-2">Précédent</span>
            </button>
            <button
              type="button"
              :disabled="!hasNextPage || loading"
              class="cds--btn cds--btn--tertiary cds--btn--sm"
              @click="nextPage"
            >
              <span class="mr-2">Suivant</span>
              <Lineicons :icon="Icons.next" :size="16" color="currentColor" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirmation de désactivation -->
    <div
      v-if="pendingDeactivation"
      class="cds--modal cds--modal--enable-presence"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="deactivate-title"
      @click.self="pendingDeactivation = null"
    >
      <div class="cds--modal-container">
        <header class="cds--modal-header">
          <h2 id="deactivate-title" class="cds--modal-header__heading">Désactiver ce compte ?</h2>
          <button
            class="cds--modal-close"
            type="button"
            aria-label="Fermer"
            @click="pendingDeactivation = null"
          >
            <Lineicons class="cds--modal-close__icon" :icon="Icons.close" :size="20" color="currentColor" />
          </button>
        </header>

        <div class="cds--modal-content">
          <p class="text-xs text-cds-text-secondary">
            <b class="text-cds-text-primary">{{ pendingDeactivation.email }}</b> ne pourra plus se connecter :
            ses jetons existants seront refusés dès la prochaine requête. Les annonces et transactions
            déjà enregistrées sont conservées pour la traçabilité.
          </p>

          <p v-if="modalError" class="mt-4 p-3 bg-cds-layer-02 border-l-2 border-cds-support-error text-cds-support-error text-xs">
            {{ modalError }}
          </p>
        </div>

        <footer class="cds--modal-footer">
          <button
            type="button"
            :disabled="togglingId !== null"
            class="cds--btn cds--btn--secondary"
            @click="pendingDeactivation = null"
          >
            Annuler
          </button>
          <button
            type="button"
            :disabled="togglingId !== null"
            class="cds--btn cds--btn--danger"
            @click="confirmDeactivate"
          >
            {{ togglingId !== null ? 'Traitement…' : 'Désactiver le compte' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { User } from '~/types'
import { roleLabel, roleBadgeClass } from '~/utils/labels'

definePageMeta({ middleware: 'admin' })

useHead({ title: 'Utilisateurs — Administration EcoLoop' })

const PAGE_SIZE = 25

const { apiFetch } = useApi()
const { user: currentUser } = useAuth()
const { formatDate, errorMessage } = useFormat()

const users = ref<User[]>([])
const loading = ref(true)
const error = ref('')
const successMessage = ref('')

const search = ref('')
const roleFilter = ref('')
const page = ref(1)

const hasNextPage = ref(false)
const togglingId = ref<string | null>(null)
const pendingDeactivation = ref<User | null>(null)
const modalError = ref('')

const currentUserId = computed(() => currentUser.value?.id || '')

const fetchUsers = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams()
    // Ne jamais envoyer `role=` vide : le backend attend un Literal, pas une chaîne vide
    if (roleFilter.value) params.set('role', roleFilter.value)
    const term = search.value.trim()
    if (term) params.set('q', term)
    params.set('limit', String(PAGE_SIZE))
    params.set('offset', String((page.value - 1) * PAGE_SIZE))

    const rows = await apiFetch<User[]>(`/admin/users?${params.toString()}`)
    users.value = rows
    hasNextPage.value = rows.length === PAGE_SIZE
  } catch (err) {
    users.value = []
    hasNextPage.value = false
    error.value = errorMessage(err, 'Impossible de charger les utilisateurs')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  page.value = 1
  fetchUsers()
}

// Recherche différée pour ne pas déclencher une requête par frappe
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 400)
})

watch(roleFilter, applyFilters)

const previousPage = () => {
  if (page.value === 1) return
  page.value -= 1
  fetchUsers()
}

const nextPage = () => {
  if (!hasNextPage.value) return
  page.value += 1
  fetchUsers()
}

const setActive = async (target: User, isActive: boolean) => {
  togglingId.value = target.id
  modalError.value = ''
  try {
    const updated = await apiFetch<User>(`/admin/users/${target.id}`, {
      method: 'PATCH',
      body: { is_active: isActive }
    })
    // Mise à jour locale : évite un aller-retour et conserve la pagination
    const index = users.value.findIndex((u) => u.id === target.id)
    if (index !== -1) users.value[index] = { ...users.value[index], ...updated }
    successMessage.value = isActive
      ? `Le compte ${target.email} a été réactivé.`
      : `Le compte ${target.email} a été désactivé.`
    pendingDeactivation.value = null
  } catch (err) {
    const message = errorMessage(err, 'Échec de la mise à jour du compte')
    if (pendingDeactivation.value) {
      modalError.value = message
    } else {
      error.value = message
    }
  } finally {
    togglingId.value = null
  }
}

const askDeactivate = (target: User) => {
  modalError.value = ''
  pendingDeactivation.value = target
}

const confirmDeactivate = async () => {
  if (!pendingDeactivation.value) return
  await setActive(pendingDeactivation.value, false)
}

onMounted(fetchUsers)

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
})
</script>
