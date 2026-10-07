<template>
  <div>
    <AdminNav />

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- En-tête de page -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Transactions</h1>
          <p class="text-xs text-cds-text-helper mt-1">
            Cycle de vie complet des enlèvements : séquestre, pesée, validation et clôture
          </p>
        </div>
        <button
          type="button"
          :disabled="loading"
          class="cds--btn cds--btn--secondary cds--btn--sm self-start"
          @click="fetchTransactions"
        >
          <span v-if="loading" class="eco-spinner w-5 h-5 mr-2"></span>
          {{ loading ? 'Chargement…' : 'Rafraîchir' }}
        </button>
      </div>

      <!-- Bandeau d'erreur : liseré latéral Carbon plutôt qu'un fond coloré -->
      <div
        v-if="error"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error text-cds-support-error text-xs flex items-start justify-between gap-4"
      >
        <span>{{ error }}</span>
        <button
          type="button"
          class="cds--btn cds--btn--danger--ghost cds--btn--sm shrink-0"
          @click="fetchTransactions"
        >
          Réessayer
        </button>
      </div>

      <!-- Filtres -->
      <div class="p-4 bg-cds-layer-01 border border-cds-border-subtle flex flex-col sm:flex-row sm:items-end gap-4">
        <div class="cds--form-item w-full sm:w-64 shrink-0">
          <label class="cds--label" for="status-filter">Statut</label>
          <div class="cds--select">
            <div class="cds--select-input__wrapper">
              <select
                id="status-filter"
                v-model="statusFilter"
                class="cds--select-input"
                @change="fetchTransactions"
              >
                <option value="">Tous les statuts</option>
                <option v-for="st in TRANSACTION_STATUSES" :key="st" :value="st">
                  {{ transactionStatusLabel(st) }}
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

        <div class="flex-1 flex flex-wrap items-center gap-4 text-xs sm:justify-end">
          <span class="text-cds-text-helper">
            Affichées : <b class="font-mono text-cds-text-secondary">{{ transactions.length }}</b>
          </span>
          <span class="text-cds-text-helper">
            Volume : <b class="font-mono text-cds-support-warning">{{ formatMoney(totalAmount) }}</b>
          </span>
          <span class="text-cds-text-helper">
            CO₂ : <b class="font-mono text-cds-link-primary">{{ formatNumber(totalCo2, 2) }} kg</b>
          </span>
        </div>
      </div>

      <!-- Squelette -->
      <div v-if="loading && !transactions.length" class="space-y-3">
        <div
          v-for="i in 5"
          :key="i"
          class="h-14 bg-cds-layer-01 border border-cds-border-subtle animate-pulse"
        ></div>
      </div>

      <!-- Tableau -->
      <div v-else class="cds--data-table-container">
        <div class="cds--data-table-content">
          <table class="cds--data-table">
            <thead>
              <tr>
                <th scope="col">Créée le</th>
                <th scope="col">Lot</th>
                <th scope="col">Parties</th>
                <th scope="col">Poids</th>
                <th scope="col">Montant</th>
                <th scope="col">CO₂ évité</th>
                <th scope="col">Statut</th>
                <th scope="col" class="!text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in transactions" :key="tx.id" class="hover:bg-cds-layer-hover-01">
                <td class="whitespace-nowrap">
                  <span class="block text-cds-text-secondary">{{ formatDate(tx.created_at) }}</span>
                  <span class="block text-[10px] font-mono text-cds-text-helper">#{{ tx.id.substring(0, 8) }}</span>
                </td>
                <td>
                  <span class="block font-semibold text-cds-text-primary max-w-[16rem] truncate" :title="tx.listing_title">
                    {{ tx.listing_title }}
                  </span>
                  <span class="block text-[10px] text-cds-text-helper">{{ tx.category_name }} · {{ tx.unit }}</span>
                </td>
                <td>
                  <span class="block text-cds-text-secondary max-w-[14rem] truncate">
                    {{ tx.producer_organization || 'Producteur particulier' }}
                  </span>
                  <span class="block text-[10px] text-cds-text-helper max-w-[14rem] truncate">
                    → {{ tx.collector_organization || 'Collecteur' }}
                  </span>
                </td>
                <td class="font-mono !text-cds-text-secondary whitespace-nowrap">
                  {{ tx.final_weight ? formatQuantity(tx.final_weight, tx.unit) : 'À peser' }}
                  <span v-if="tx.agreed_quantity" class="block text-[10px] text-cds-text-helper">
                    prévu {{ formatQuantity(tx.agreed_quantity, tx.unit) }}
                  </span>
                </td>
                <td class="font-mono whitespace-nowrap">
                  <span :class="tx.total_amount ? 'text-cds-support-warning' : 'text-cds-text-helper'">
                    {{ formatMoney(tx.total_amount) }}
                  </span>
                </td>
                <td class="font-mono !text-cds-link-primary whitespace-nowrap">
                  {{ tx.co2_saved_total ? formatNumber(tx.co2_saved_total, 2) + ' kg' : '—' }}
                </td>
                <td>
                  <span class="cds--tag whitespace-nowrap" :class="transactionStatusBadgeClass(tx.payment_status)">
                    {{ transactionStatusLabel(tx.payment_status) }}
                  </span>
                  <span v-if="tx.bsdd_number" class="block text-[10px] font-mono text-cds-text-helper mt-1">
                    {{ tx.bsdd_number }}
                  </span>
                </td>
                <td class="!text-right">
                  <NuxtLink
                    :to="`/transactions/${tx.id}`"
                    class="cds--btn cds--btn--ghost cds--btn--sm whitespace-nowrap"
                  >
                    Détails
                  </NuxtLink>
                </td>
              </tr>
              <tr v-if="!transactions.length">
                <td colspan="8" class="py-12 !text-center !text-cds-text-helper">
                  Aucune transaction pour ce filtre.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="px-4 py-3 border-t border-cds-border-subtle text-[10px] text-cds-text-helper">
          L'API renvoie au maximum les 200 transactions les plus récentes.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { Transaction } from '~/types'
import {
  TRANSACTION_STATUSES,
  transactionStatusLabel,
  transactionStatusBadgeClass
} from '~/utils/labels'

definePageMeta({ middleware: 'admin' })

useHead({ title: 'Transactions — Administration EcoLoop' })

const { apiFetch } = useApi()
const { formatNumber, formatMoney, formatQuantity, formatDate, toNumber, errorMessage } = useFormat()

const transactions = ref<Transaction[]>([])
const statusFilter = ref('')
const loading = ref(true)
const error = ref('')

const totalAmount = computed(() =>
  transactions.value.reduce((sum, tx) => sum + (toNumber(tx.total_amount) || 0), 0)
)

const totalCo2 = computed(() =>
  transactions.value.reduce((sum, tx) => sum + (toNumber(tx.co2_saved_total) || 0), 0)
)

const fetchTransactions = async () => {
  loading.value = true
  error.value = ''
  try {
    const query = statusFilter.value ? `?status=${encodeURIComponent(statusFilter.value)}` : ''
    transactions.value = await apiFetch<Transaction[]>(`/transactions${query}`)
  } catch (err) {
    transactions.value = []
    error.value = errorMessage(err, 'Impossible de charger les transactions')
  } finally {
    loading.value = false
  }
}

onMounted(fetchTransactions)
</script>
