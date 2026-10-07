<template>
  <div>
    <AdminNav :dispute-count="stats?.open_disputes || 0" />

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- En-tête -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Supervision de la plateforme</h1>
          <p class="text-xs text-cds-text-helper mt-1">
            Indicateurs consolidés sur l'ensemble des producteurs, collecteurs et transactions
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <span class="eco-chip">
            Vue : <b class="text-cds-link-visited ml-1">Administrateur</b>
          </span>
          <button
            type="button"
            :disabled="loading"
            class="cds--btn cds--btn--tertiary cds--btn--sm"
            @click="fetchStats"
          >
            {{ loading ? 'Chargement…' : 'Rafraîchir' }}
          </button>
        </div>
      </div>

      <!-- Erreur -->
      <div
        v-if="error"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error text-xs flex items-start justify-between gap-4"
      >
        <span class="text-cds-text-secondary">{{ error }}</span>
        <button
          type="button"
          class="cds--btn cds--btn--ghost cds--btn--sm shrink-0"
          @click="fetchStats"
        >
          Réessayer
        </button>
      </div>

      <!-- Alerte litiges -->
      <NuxtLink
        v-if="stats && stats.open_disputes > 0"
        to="/admin/disputes"
        class="block p-4 bg-cds-layer-01 border-l-2 border-cds-support-warning hover:bg-cds-layer-hover-01 transition group"
      >
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center space-x-3">
            <span class="p-2 bg-cds-layer-02 text-cds-support-warning">
              <Lineicons :icon="Icons.error" :size="20" color="currentColor" />
            </span>
            <div>
              <p class="text-sm font-bold text-cds-support-warning">
                {{ stats.open_disputes }} litige{{ stats.open_disputes > 1 ? 's' : '' }} en attente d'arbitrage
              </p>
              <p class="text-[11px] text-cds-text-helper">
                Les fonds restent séquestrés tant qu'aucune décision n'est rendue.
              </p>
            </div>
          </div>
          <span class="text-xs font-semibold text-cds-link-primary group-hover:underline shrink-0">Arbitrer →</span>
        </div>
      </NuxtLink>

      <!-- Squelette de chargement -->
      <div v-if="loading && !stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="h-36 bg-cds-layer-01 border border-cds-border-subtle animate-pulse"></div>
      </div>

      <template v-if="stats">
        <!-- KPI principaux -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">CO₂ évité</span>
              <div class="p-2 bg-cds-layer-02 text-cds-link-primary">
                <Lineicons :icon="Icons.co2" :size="20" color="currentColor" />
              </div>
            </div>
            <div class="mt-4 flex items-baseline space-x-2">
              <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(stats.total_co2_saved_kg, 2) }}</span>
              <span class="text-xs font-bold text-cds-link-primary">kg CO₂e</span>
            </div>
            <p class="text-[11px] text-cds-text-helper mt-2">
              ≈ {{ formatNumber(stats.trees_equivalent, 1) }} arbres absorbants / an
            </p>
          </div>

          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Matière valorisée</span>
              <div class="p-2 bg-cds-layer-02 text-cds-support-info">
                <Lineicons :icon="Icons.material" :size="20" color="currentColor" />
              </div>
            </div>
            <div class="mt-4 flex items-baseline space-x-2">
              <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(stats.total_quantity_kg, 2) }}</span>
              <span class="text-xs font-bold text-cds-support-info">kg</span>
            </div>
            <p class="text-[11px] text-cds-text-helper mt-2">Tonnages convertis en kg (huiles ≈ kg)</p>
          </div>

          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Volume financier</span>
              <div class="p-2 bg-cds-layer-02 text-cds-support-warning">
                <Lineicons :icon="Icons.money" :size="20" color="currentColor" />
              </div>
            </div>
            <div class="mt-4 flex items-baseline space-x-2">
              <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(stats.total_financial_volume, 0) }}</span>
              <span class="text-xs font-bold text-cds-support-warning">FCFA</span>
            </div>
            <p class="text-[11px] text-cds-text-helper mt-2">Transactions honorées (statut « payé »)</p>
          </div>

          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Deals clôturés</span>
              <div class="p-2 bg-cds-layer-02 text-cds-support-success">
                <Lineicons :icon="Icons.success" :size="20" color="currentColor" />
              </div>
            </div>
            <div class="mt-4 flex items-baseline space-x-2">
              <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(stats.completed_transactions, 0) }}</span>
              <span class="text-xs font-bold text-cds-support-success">bordereaux</span>
            </div>
            <p class="text-[11px] text-cds-text-helper mt-2">
              <NuxtLink to="/admin/disputes" class="text-cds-support-error hover:underline font-semibold">
                {{ stats.open_disputes }} litige{{ stats.open_disputes > 1 ? 's' : '' }} ouvert{{ stats.open_disputes > 1 ? 's' : '' }}
              </NuxtLink>
            </p>
          </div>
        </div>

        <!-- Répartitions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-bold text-cds-text-primary">Communauté par rôle</h2>
              <NuxtLink to="/admin/users" class="text-[11px] font-semibold text-cds-link-primary hover:underline">
                Gérer →
              </NuxtLink>
            </div>
            <ul class="space-y-3">
              <li v-for="row in usersByRole" :key="row.key">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="font-semibold text-cds-text-secondary">{{ row.label }}</span>
                  <span class="font-mono text-cds-text-helper">{{ formatNumber(row.count, 0) }}</span>
                </div>
                <div class="h-1.5 rounded-full bg-cds-layer-02 overflow-hidden">
                  <div class="h-full rounded-full" :class="row.bar" :style="{ width: row.percent + '%' }"></div>
                </div>
              </li>
              <li v-if="!usersByRole.length" class="py-6 text-center text-xs text-cds-text-helper">Aucun utilisateur.</li>
            </ul>
          </div>

          <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-bold text-cds-text-primary">Annonces par statut</h2>
              <span class="text-[11px] text-cds-text-helper">
                {{ formatNumber(totalListings, 0) }} annonce{{ totalListings > 1 ? 's' : '' }}
              </span>
            </div>
            <ul class="space-y-3">
              <li v-for="row in listingsByStatus" :key="row.key">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="font-semibold text-cds-text-secondary">{{ row.label }}</span>
                  <span class="font-mono text-cds-text-helper">{{ formatNumber(row.count, 0) }}</span>
                </div>
                <div class="h-1.5 rounded-full bg-cds-layer-02 overflow-hidden">
                  <div class="h-full rounded-full" :class="row.bar" :style="{ width: row.percent + '%' }"></div>
                </div>
              </li>
              <li v-if="!listingsByStatus.length" class="py-6 text-center text-xs text-cds-text-helper">Aucune annonce.</li>
            </ul>
          </div>
        </div>

        <!-- Impact par matière -->
        <div class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8">
          <h2 class="text-lg font-bold text-cds-text-primary mb-4">Impact consolidé par flux de matière</h2>
          <div class="overflow-x-auto">
            <div class="cds--data-table-container">
              <table class="cds--data-table">
                <thead>
                  <tr>
                    <th scope="col">Matière</th>
                    <th scope="col">Quantité</th>
                    <th scope="col">CO₂ évité</th>
                    <th scope="col">Volume financier</th>
                    <th scope="col">Transactions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in stats.by_material" :key="item.category_slug">
                    <td class="font-semibold !text-cds-text-primary">
                      <span class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-cds-support-success shrink-0"></span>
                        <span>{{ item.category_name }}</span>
                      </span>
                    </td>
                    <td class="font-mono !text-cds-text-secondary">
                      {{ formatQuantity(item.total_quantity, item.unit) }}
                    </td>
                    <td class="font-mono font-semibold !text-cds-link-primary">{{ formatCo2(item.co2_saved) }}</td>
                    <td class="font-mono !text-cds-text-secondary">{{ formatMoney(item.financial_volume) }}</td>
                    <td class="!text-cds-text-helper">{{ formatNumber(item.transactions_count, 0) }}</td>
                  </tr>
                  <tr v-if="!stats.by_material.length">
                    <td colspan="5" class="py-8 !text-center !text-cds-text-helper">
                      Aucune transaction clôturée sur la plateforme.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { GlobalStats } from '~/types'
import { ROLE_LABELS, LISTING_STATUS_LABELS } from '~/utils/labels'

definePageMeta({ middleware: 'admin' })

useHead({ title: "Administration — EcoLoop" })

const { apiFetch } = useApi()
const { formatNumber, formatMoney, formatQuantity, formatCo2, errorMessage } = useFormat()

const stats = ref<GlobalStats | null>(null)
const loading = ref(true)
const error = ref('')

const ROLE_ORDER = ['producer', 'collector', 'admin']
/**
 * Barres de progression : seuls les jetons de support Carbon sont utilisés
 * (aucune couleur en dur), le thème clair/sombre suit donc --cds-*.
 */
const ROLE_BARS: Record<string, string> = {
  producer: 'bg-cds-support-info',
  collector: 'bg-cds-support-warning',
  admin: 'bg-cds-link-visited'
}

const LISTING_ORDER = ['published', 'reserved', 'in_transit', 'completed', 'draft', 'cancelled']
const LISTING_BARS: Record<string, string> = {
  published: 'bg-cds-support-success',
  reserved: 'bg-cds-support-warning',
  in_transit: 'bg-cds-support-info',
  completed: 'bg-cds-border-strong',
  draft: 'bg-cds-border-strong',
  cancelled: 'bg-cds-support-error'
}

const totalListings = computed(() =>
  Object.values(stats.value?.listings_by_status || {}).reduce((sum, n) => sum + n, 0)
)

/** Ordonne les clés connues puis conserve les éventuelles clés imprévues. */
const sortKeys = (counts: Record<string, number>, order: string[]): string[] => {
  const known = order.filter((k) => k in counts)
  const extra = Object.keys(counts).filter((k) => !order.includes(k))
  return [...known, ...extra]
}

const toRows = (
  counts: Record<string, number> | undefined,
  order: string[],
  labels: Record<string, string>,
  bars: Record<string, string>
) => {
  const data = counts || {}
  const max = Math.max(1, ...Object.values(data))
  return sortKeys(data, order).map((key) => ({
    key,
    label: labels[key] || key,
    count: data[key] || 0,
    percent: Math.round(((data[key] || 0) / max) * 100),
    bar: bars[key] || 'bg-cds-border-strong'
  }))
}

const usersByRole = computed(() =>
  toRows(stats.value?.users_by_role, ROLE_ORDER, ROLE_LABELS, ROLE_BARS)
)

const listingsByStatus = computed(() =>
  toRows(stats.value?.listings_by_status, LISTING_ORDER, LISTING_STATUS_LABELS, LISTING_BARS)
)

const fetchStats = async () => {
  loading.value = true
  error.value = ''
  try {
    stats.value = await apiFetch<GlobalStats>('/analytics/global')
  } catch (err) {
    error.value = errorMessage(err, 'Impossible de charger les statistiques globales')
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>
