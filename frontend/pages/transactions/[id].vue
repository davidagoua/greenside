<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <div v-if="loading" class="py-24 flex justify-center">
      <div class="w-10 h-10 border-4 border-eco-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else-if="!transaction" class="p-8 text-center bg-slate-900 border border-slate-800 rounded-3xl">
      <p class="text-sm text-slate-400">Transaction introuvable</p>
      <NuxtLink to="/marketplace" class="mt-4 inline-block px-4 py-2 bg-eco-600 text-white rounded-xl text-xs font-semibold">
        Retour au marché
      </NuxtLink>
    </div>

    <div v-else class="space-y-6">
      <!-- Deal Header -->
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-mono text-slate-500">#{{ transaction.id.substring(0, 8) }}</span>
              <span
                class="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider"
                :class="statusBadgeClass(transaction.payment_status)"
              >
                {{ statusLabel(transaction.payment_status) }}
              </span>
            </div>
            <h1 class="text-2xl font-bold text-white mt-1">{{ transaction.listing_title }}</h1>
            <p class="text-xs text-slate-400 mt-1">
              Catégorie : <b class="text-slate-200">{{ transaction.category_name }}</b> • Lieu : 📍 {{ transaction.address_text }}
            </p>
          </div>

          <!-- BSDD Download Button if available -->
          <div v-if="transaction.bsdd_number" class="flex sm:flex-col gap-2">
            <button
              @click="downloadBsdd('pdf')"
              type="button"
              class="px-4 py-2 rounded-xl bg-eco-600 hover:bg-eco-500 text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-lg shadow-eco-600/20"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>BSDD (PDF)</span>
            </button>

            <button
              @click="downloadBsdd('json')"
              type="button"
              class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              Format JSON
            </button>
          </div>
        </div>

        <!-- Deal Parties & Escrow details -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 text-xs">
          <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block mb-1">Producteur (Remettant)</span>
            <span class="font-bold text-white block">{{ transaction.producer_organization || 'Producteur particulier' }}</span>
            <span class="text-slate-400">{{ transaction.producer_phone }}</span>
          </div>

          <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block mb-1">Collecteur (Repreneur)</span>
            <span class="font-bold text-white block">{{ transaction.collector_organization || 'Collecteur' }}</span>
            <span class="text-slate-400">{{ transaction.collector_phone }}</span>
          </div>

          <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block mb-1">Séquestre / Escrow</span>
            <span class="font-mono text-eco-400 font-bold block">{{ transaction.escrow_reference || 'En attente' }}</span>
            <span class="text-slate-300">
              Total : {{ transaction.total_amount ? transaction.total_amount.toLocaleString() + ' FCFA' : 'À peser' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Action Area depending on role and status -->

      <!-- 1. PRODUCER VIEW: QR Code Display for Field Collector to scan -->
      <div
        v-if="transaction.viewer_role === 'producer' && transaction.payment_status === 'escrow_locked'"
        class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8"
      >
        <div class="text-center max-w-md mx-auto">
          <h2 class="text-lg font-bold text-white">Présenter ce QR Code au collecteur</h2>
          <p class="text-xs text-slate-400 mt-1 mb-6">
            Le collecteur doit scanner ce QR code sur place avec son smartphone avant d'effectuer la pesée contradictoire
          </p>

          <ClientOnly>
            <QrCodeViewer
              v-if="qrData"
              :value="qrData.payload"
              :token="qrData.token"
            />
          </ClientOnly>
        </div>
      </div>

      <!-- 2. PRODUCER VIEW: Final Confirmation of weighing -->
      <div
        v-if="transaction.viewer_role === 'producer' && transaction.payment_status === 'collected_pending_verification'"
        class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8"
      >
        <div class="max-w-md mx-auto text-center space-y-4">
          <div class="w-12 h-12 rounded-full bg-eco-500/10 text-eco-400 mx-auto flex items-center justify-center">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 class="text-lg font-bold text-white">Pesée enregistrée par le collecteur</h2>
          <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-left space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-slate-400">Poids constaté :</span>
              <span class="font-bold text-white">{{ transaction.final_weight }} {{ transaction.unit }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Montant net à débloquer :</span>
              <span class="font-bold text-eco-400">{{ transaction.total_amount?.toLocaleString() }} FCFA</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">CO₂ évité estimé :</span>
              <span class="font-bold text-eco-400">{{ transaction.co2_saved_total }} kg CO₂e</span>
            </div>
          </div>

          <div v-if="transaction.weighing_proof_url" class="mt-3">
            <span class="text-xs text-slate-400 block mb-1">Preuve de pesée (balance / ticket) :</span>
            <img :src="transaction.weighing_proof_url" class="w-32 h-32 object-cover rounded-xl mx-auto border border-slate-800" />
          </div>

          <div class="flex space-x-3 pt-2">
            <button
              @click="openDisputeModal = true"
              type="button"
              class="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
            >
              Signaler un litige
            </button>
            <button
              @click="confirmCollection"
              :disabled="actionLoading"
              type="button"
              class="flex-1 py-3 rounded-xl bg-eco-600 hover:bg-eco-500 text-white text-xs font-bold transition shadow-lg shadow-eco-600/20 disabled:opacity-50"
            >
              {{ actionLoading ? 'Déblocage...' : 'Valider & Débloquer fonds' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 3. COLLECTOR VIEW: Scanner QR & Saisie de pesée -->
      <div
        v-if="transaction.viewer_role === 'collector' && transaction.payment_status === 'escrow_locked'"
        class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6"
      >
        <h2 class="text-lg font-bold text-white text-center">Étape terrain : Scan & Pesée</h2>

        <!-- Tab between Camera Scan & Manual Token -->
        <div class="max-w-md mx-auto space-y-6">
          <div v-if="!scannedToken" class="space-y-4">
            <ClientOnly>
              <QrScanner @scan="handleScanResult" />
            </ClientOnly>

            <div class="text-center">
              <span class="text-xs text-slate-500">ou saisie manuelle du token de sécurité</span>
              <div class="mt-2 flex space-x-2">
                <input
                  v-model="manualToken"
                  type="text"
                  placeholder="Collez le token du QR code..."
                  class="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs font-mono"
                />
                <button
                  @click="scannedToken = manualToken"
                  type="button"
                  class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
                >
                  OK
                </button>
              </div>
            </div>
          </div>

          <!-- Once token verified / scanned, show weighing form -->
          <div v-else class="p-6 rounded-2xl bg-slate-950 border border-eco-500/40 space-y-4">
            <div class="flex items-center space-x-2 text-eco-400 text-xs font-semibold">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span>QR code validé avec succès</span>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">
                Poids réel constaté sur la balance ({{ transaction.unit }})
              </label>
              <input
                v-model.number="weighingForm.final_weight"
                type="number"
                step="0.01"
                min="0.1"
                required
                class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-eco-500 font-mono font-bold"
              />
            </div>

            <!-- Weighing proof photo -->
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">
                Photo justificative (ticket ou affichage balance)
              </label>
              <input
                type="file"
                ref="proofInputRef"
                accept="image/*"
                @change="handleProofUpload"
                class="hidden"
              />
              <button
                @click="proofInputRef?.click()"
                type="button"
                :disabled="uploadingProof"
                class="w-full py-2.5 rounded-xl bg-slate-900 border border-dashed border-slate-700 text-slate-300 text-xs font-medium hover:border-eco-500 transition"
              >
                {{ uploadingProof ? 'Téléversement en cours...' : (weighingForm.weighing_proof_url ? '✓ Photo ajoutée (changer)' : '+ Prendre une photo du ticket') }}
              </button>
            </div>

            <button
              @click="submitWeighing"
              :disabled="actionLoading"
              type="button"
              class="w-full py-3 rounded-xl bg-eco-600 hover:bg-eco-500 text-white text-xs font-bold transition shadow-lg shadow-eco-600/20 disabled:opacity-50"
            >
              {{ actionLoading ? 'Enregistrement...' : 'Enregistrer la pesée contradictoire' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Dispute Modal -->
    <div v-if="openDisputeModal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
        <h3 class="text-lg font-bold text-white">Ouvrir un litige</h3>
        <p class="text-xs text-slate-400 mt-1">Expliquez le problème pour arbitrage par un administrateur.</p>

        <textarea
          v-model="disputeReason"
          rows="4"
          required
          placeholder="Ex: Écart de poids injustifié, matière non conforme..."
          class="w-full mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-red-500"
        ></textarea>

        <div class="mt-6 flex space-x-3">
          <button
            @click="openDisputeModal = false"
            type="button"
            class="flex-1 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
          >
            Annuler
          </button>
          <button
            @click="submitDispute"
            :disabled="actionLoading || !disputeReason"
            type="button"
            class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold disabled:opacity-50"
          >
            Déclarer le litige
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { Transaction } from '~/types'

const route = useRoute()
const txId = route.params.id as string
const { apiFetch } = useApi()

const transaction = ref<Transaction | null>(null)
const qrData = ref<{ transaction_id: string; token: string; payload: string } | null>(null)
const loading = ref(true)
const actionLoading = ref(false)
const scannedToken = ref('')
const manualToken = ref('')
const uploadingProof = ref(false)
const proofInputRef = ref<HTMLInputElement | null>(null)
const openDisputeModal = ref(false)
const disputeReason = ref('')

const weighingForm = reactive({
  final_weight: 100,
  weighing_proof_url: ''
})

const fetchTransaction = async () => {
  try {
    transaction.value = await apiFetch<Transaction>(`/transactions/${txId}`)
    if (transaction.value.viewer_role === 'producer' && transaction.value.payment_status === 'escrow_locked') {
      qrData.value = await apiFetch<any>(`/transactions/${txId}/qr`)
    }
  } catch (err) {
    console.error('Erreur chargement transaction:', err)
  } finally {
    loading.value = false
  }
}

const handleScanResult = (result: string) => {
  // Extract token from URL if it's a URL or use raw text
  try {
    const url = new URL(result)
    const tok = url.searchParams.get('token')
    scannedToken.value = tok || result
  } catch (e) {
    scannedToken.value = result
  }
}

const handleProofUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadingProof.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', 'weighing')
    const res = await apiFetch<any>('/media/upload', {
      method: 'POST',
      body: formData
    })
    weighingForm.weighing_proof_url = res.url
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur upload preuve')
  } finally {
    uploadingProof.value = false
  }
}

const submitWeighing = async () => {
  actionLoading.value = true
  try {
    await apiFetch(`/transactions/${txId}/collect`, {
      method: 'POST',
      body: {
        token: scannedToken.value,
        final_weight: weighingForm.final_weight,
        weighing_proof_url: weighingForm.weighing_proof_url || null
      }
    })
    await fetchTransaction()
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur pesée')
  } finally {
    actionLoading.value = false
  }
}

const confirmCollection = async () => {
  actionLoading.value = true
  try {
    await apiFetch(`/transactions/${txId}/confirm`, {
      method: 'POST'
    })
    await fetchTransaction()
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur validation')
  } finally {
    actionLoading.value = false
  }
}

const submitDispute = async () => {
  actionLoading.value = true
  try {
    await apiFetch(`/transactions/${txId}/dispute`, {
      method: 'POST',
      body: { reason: disputeReason.value }
    })
    openDisputeModal.value = false
    await fetchTransaction()
  } catch (err: any) {
    alert(err.response?._data?.detail || err.message || 'Erreur déclaration litige')
  } finally {
    actionLoading.value = false
  }
}

const downloadBsdd = async (format: 'pdf' | 'json') => {
  const config = useRuntimeConfig()
  const { token } = useAuth()
  const res = await fetch(`${config.public.apiBaseUrl}/transactions/${txId}/bsdd?format=${format}`, {
    headers: { Authorization: `Bearer ${token.value}` }
  })
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${transaction.value?.bsdd_number || 'BSDD'}.${format}`
  a.click()
  window.URL.revokeObjectURL(url)
}

const statusLabel = (st: string) => {
  switch (st) {
    case 'escrow_locked': return 'Fonds sous séquestre'
    case 'collected_pending_verification': return 'Pesée en attente de validation'
    case 'paid': return 'Clôturé & Payé'
    case 'disputed': return 'Litige ouvert'
    case 'cancelled': return 'Annulé'
    default: return st
  }
}

const statusBadgeClass = (st: string) => {
  switch (st) {
    case 'escrow_locked': return 'bg-amber-950/80 border border-amber-500/40 text-amber-300'
    case 'collected_pending_verification': return 'bg-cyan-950/80 border border-cyan-500/40 text-cyan-300'
    case 'paid': return 'bg-eco-950/80 border border-eco-500/40 text-eco-300'
    case 'disputed': return 'bg-red-950/80 border border-red-500/40 text-red-300'
    default: return 'bg-slate-800 text-slate-300'
  }
}

onMounted(() => {
  fetchTransaction()
})
</script>
