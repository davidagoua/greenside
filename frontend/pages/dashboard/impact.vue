<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Tableau de bord Impact RSE & Climat</h1>
        <p class="text-xs text-cds-text-helper mt-1">
          Mesure d'évitement carbone, valorisation circulaire et traçabilité réglementaire
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <span class="eco-chip">
          Vue : <b class="text-cds-link-primary capitalize ml-1">{{ user?.role || 'Visiteur' }}</b>
        </span>
      </div>
    </div>

    <!-- Chargement -->
    <div v-if="loading" class="flex justify-center py-12">
      <span class="eco-spinner w-8 h-8"></span>
    </div>

    <template v-else>
      <!-- Impact Cards Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Card 1: CO2 Avoided -->
        <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">CO₂ Évité</span>
            <div class="p-2 bg-cds-layer-02 text-cds-link-primary">
              <Lineicons :icon="Icons.co2" :size="20" color="currentColor" />
            </div>
          </div>
          <div class="mt-4 flex items-baseline space-x-2">
            <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(impact?.total_co2_saved_kg, 2) }}</span>
            <span class="text-xs font-bold text-cds-link-primary">kg CO₂e</span>
          </div>
          <p class="text-[11px] text-cds-text-helper mt-2">Calculé selon facteurs ADEME & GHG Protocol</p>
        </div>

        <!-- Card 2: Recycled Volume -->
        <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Matière Valorisée</span>
            <div class="p-2 bg-cds-layer-02 text-cds-support-info">
              <Lineicons :icon="Icons.material" :size="20" color="currentColor" />
            </div>
          </div>
          <div class="mt-4 flex items-baseline space-x-2">
            <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(impact?.total_quantity_kg, 2) }}</span>
            <span class="text-xs font-bold text-cds-support-info">kg</span>
          </div>
          <p class="text-[11px] text-cds-text-helper mt-2">Déchets détournés des décharges</p>
        </div>

        <!-- Card 3: Trees Equivalent -->
        <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Équivalent Arbres</span>
            <div class="p-2 bg-cds-layer-02 text-cds-support-success">
              <Lineicons :icon="Icons.trees" :size="20" color="currentColor" />
            </div>
          </div>
          <div class="mt-4 flex items-baseline space-x-2">
            <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(impact?.trees_equivalent, 0) }}</span>
            <span class="text-xs font-bold text-cds-support-success">arbres / an</span>
          </div>
          <p class="text-[11px] text-cds-text-helper mt-2">Absorption équivalente (25 kg/an/arbre)</p>
        </div>

        <!-- Card 4: Deals closed -->
        <div class="p-6 bg-cds-layer-01 border border-cds-border-subtle">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-cds-text-helper uppercase tracking-wider">Deals Clôturés</span>
            <div class="p-2 bg-cds-layer-02 text-cds-support-warning">
              <Lineicons :icon="Icons.success" :size="20" color="currentColor" />
            </div>
          </div>
          <div class="mt-4 flex items-baseline space-x-2">
            <span class="text-3xl font-extrabold text-cds-text-primary font-mono">{{ formatNumber(impact?.completed_transactions, 0) }}</span>
            <span class="text-xs font-bold text-cds-support-warning">bordereaux BSDD</span>
          </div>
          <p class="text-[11px] text-cds-text-helper mt-2">
            Volume : {{ formatMoney(impact?.total_financial_volume) }}
          </p>
        </div>
      </div>

      <!-- Breakdown By Material Table -->
      <div class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8">
        <h2 class="text-lg font-bold text-cds-text-primary mb-4">Répartition et évitement par flux de matière</h2>

        <div class="overflow-x-auto">
          <div class="cds--data-table-container">
            <table class="cds--data-table">
              <thead>
                <tr>
                  <th scope="col">Matière</th>
                  <th scope="col">Quantité collectée</th>
                  <th scope="col">CO₂ évité</th>
                  <th scope="col">Volume financier</th>
                  <th scope="col">Transactions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in impact?.by_material" :key="item.category_slug">
                  <td class="font-semibold !text-cds-text-primary">
                    <span class="flex items-center space-x-2">
                      <span class="w-2.5 h-2.5 rounded-full bg-cds-support-success shrink-0"></span>
                      <span>{{ item.category_name }}</span>
                    </span>
                  </td>
                  <td class="font-mono !text-cds-text-secondary">
                    {{ formatQuantity(item.total_quantity, item.unit) }}
                  </td>
                  <td class="font-mono font-semibold !text-cds-link-primary">
                    {{ formatCo2(item.co2_saved) }}
                  </td>
                  <td class="font-mono !text-cds-text-secondary">
                    {{ formatMoney(item.financial_volume) }}
                  </td>
                  <td class="!text-cds-text-helper">
                    {{ formatNumber(item.transactions_count, 0) }}
                  </td>
                </tr>
                <tr v-if="!impact?.by_material?.length">
                  <td colspan="5" class="py-8 !text-center !text-cds-text-helper">
                    Aucune transaction clôturée pour le moment.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { ImpactData } from '~/types'

const { user } = useAuth()
const { apiFetch } = useApi()
const { formatNumber, formatMoney, formatQuantity, formatCo2 } = useFormat()

const impact = ref<ImpactData | null>(null)
const loading = ref(true)

const fetchImpact = async () => {
  try {
    const endpoint = user.value?.role === 'collector'
      ? '/analytics/collector/impact'
      : '/analytics/producer/impact'
    impact.value = await apiFetch<ImpactData>(endpoint)
  } catch (err) {
    console.error('Erreur chargement analytics:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchImpact()
})
</script>
