<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-white tracking-tight">Tableau de bord Impact RSE & Climat</h1>
        <p class="text-xs text-slate-400 mt-1">
          Mesure d'évitement carbone, valorisation circulaire et traçabilité réglementaire
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <span class="text-xs px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
          Vue : <b class="text-eco-400 capitalize">{{ user?.role || 'Visiteur' }}</b>
        </span>
      </div>
    </div>

    <!-- Impact Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Card 1: CO2 Avoided -->
      <div class="p-6 rounded-3xl bg-slate-900 border border-slate-800 relative overflow-hidden shadow-lg">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">CO₂ Évité</span>
          <div class="p-2 rounded-xl bg-eco-500/10 text-eco-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
            </svg>
          </div>
        </div>
        <div class="mt-4 flex items-baseline space-x-2">
          <span class="text-3xl font-extrabold text-white font-mono">{{ impact?.total_co2_saved_kg.toLocaleString() || '0' }}</span>
          <span class="text-xs font-bold text-eco-400">kg CO₂e</span>
        </div>
        <p class="text-[11px] text-slate-500 mt-2">Calculé selon facteurs ADEME & GHG Protocol</p>
      </div>

      <!-- Card 2: Recycled Volume -->
      <div class="p-6 rounded-3xl bg-slate-900 border border-slate-800 relative overflow-hidden shadow-lg">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Matière Valorisée</span>
          <div class="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
        </div>
        <div class="mt-4 flex items-baseline space-x-2">
          <span class="text-3xl font-extrabold text-white font-mono">{{ impact?.total_quantity_kg.toLocaleString() || '0' }}</span>
          <span class="text-xs font-bold text-cyan-400">kg</span>
        </div>
        <p class="text-[11px] text-slate-500 mt-2">Déchets détournés des décharges</p>
      </div>

      <!-- Card 3: Trees Equivalent -->
      <div class="p-6 rounded-3xl bg-slate-900 border border-slate-800 relative overflow-hidden shadow-lg">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Équivalent Arbres</span>
          <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
        </div>
        <div class="mt-4 flex items-baseline space-x-2">
          <span class="text-3xl font-extrabold text-white font-mono">{{ impact?.trees_equivalent || '0' }}</span>
          <span class="text-xs font-bold text-emerald-400">arbres / an</span>
        </div>
        <p class="text-[11px] text-slate-500 mt-2">Absorption équivalente (25 kg/an/arbre)</p>
      </div>

      <!-- Card 4: Deals closed -->
      <div class="p-6 rounded-3xl bg-slate-900 border border-slate-800 relative overflow-hidden shadow-lg">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Deals Clôturés</span>
          <div class="p-2 rounded-xl bg-amber-500/10 text-amber-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <div class="mt-4 flex items-baseline space-x-2">
          <span class="text-3xl font-extrabold text-white font-mono">{{ impact?.completed_transactions || '0' }}</span>
          <span class="text-xs font-bold text-amber-400">bordereaux BSDD</span>
        </div>
        <p class="text-[11px] text-slate-500 mt-2">Volume : {{ impact?.total_financial_volume.toLocaleString() }} FCFA</p>
      </div>
    </div>

    <!-- Breakdown By Material Table -->
    <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
      <h2 class="text-lg font-bold text-white mb-4">Répartition et évitement par flux de matière</h2>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
              <th class="py-3 px-4">Matière</th>
              <th class="py-3 px-4">Quantité collectée</th>
              <th class="py-3 px-4">CO₂ évité</th>
              <th class="py-3 px-4">Volume financier</th>
              <th class="py-3 px-4">Transactions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60">
            <tr v-for="item in impact?.by_material" :key="item.category_slug" class="hover:bg-slate-850/50">
              <td class="py-3 px-4 font-bold text-white flex items-center space-x-2">
                <span class="w-2.5 h-2.5 rounded-full bg-eco-500"></span>
                <span>{{ item.category_name }}</span>
              </td>
              <td class="py-3 px-4 font-mono font-medium text-slate-200">
                {{ item.total_quantity }} {{ item.unit }}
              </td>
              <td class="py-3 px-4 font-mono text-eco-400 font-bold">
                {{ item.co2_saved }} kg CO₂e
              </td>
              <td class="py-3 px-4 font-mono text-slate-300">
                {{ item.financial_volume.toLocaleString() }} FCFA
              </td>
              <td class="py-3 px-4 text-slate-400">
                {{ item.transactions_count }}
              </td>
            </tr>
            <tr v-if="!impact?.by_material?.length">
              <td colspan="5" class="py-8 text-center text-slate-500">
                Aucune transaction clôturée pour le moment.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { ImpactData } from '~/types'

const { user } = useAuth()
const { apiFetch } = useApi()

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
