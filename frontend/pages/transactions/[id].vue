<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <div v-if="loading" class="py-24 flex justify-center">
      <span class="eco-spinner w-10 h-10"></span>
    </div>

    <div v-else-if="!transaction" class="p-8 text-center bg-cds-layer-01 border border-cds-border-subtle">
      <p class="text-sm text-cds-text-helper">Transaction introuvable</p>
      <NuxtLink to="/marketplace" class="cds--btn cds--btn--primary mt-4">
        Retour au marché
      </NuxtLink>
    </div>

    <div v-else class="space-y-6">
      <!-- Deal Header -->
      <div class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-cds-border-subtle">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-mono text-cds-text-helper">#{{ transaction.id.substring(0, 8) }}</span>
              <!-- Étiquette de statut Carbon : la couleur porte le sens métier -->
              <span
                class="cds--tag"
                :class="transactionStatusBadgeClass(transaction.payment_status)"
              >
                {{ transactionStatusLabel(transaction.payment_status) }}
              </span>
            </div>
            <h1 class="text-2xl font-bold text-cds-text-primary mt-1">{{ transaction.listing_title }}</h1>
            <p class="text-xs text-cds-text-helper mt-1 flex flex-wrap items-center gap-1">
              <span>Catégorie : <b class="text-cds-text-secondary">{{ transaction.category_name }}</b></span>
              <span>•</span>
              <span>Lieu :</span>
              <Lineicons :icon="Icons.location" :size="14" color="currentColor" />
              <span>{{ transaction.address_text }}</span>
            </p>
          </div>

          <!-- BSDD Download Button if available -->
          <div v-if="transaction.bsdd_number" class="flex sm:flex-col gap-2">
            <button
              @click="downloadBsdd('pdf')"
              type="button"
              class="cds--btn cds--btn--primary"
            >
              <Lineicons :icon="Icons.download" :size="16" color="currentColor" />
              <span class="ml-2">BSDD (PDF)</span>
            </button>

            <button
              @click="downloadBsdd('json')"
              type="button"
              class="cds--btn cds--btn--tertiary"
            >
              Format JSON
            </button>
          </div>
        </div>

        <!-- Deal Parties & Escrow details -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 text-xs">
          <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
            <span class="text-cds-text-helper block mb-1">Producteur (Remettant)</span>
            <span class="font-bold text-cds-text-primary block">{{ transaction.producer_organization || 'Producteur particulier' }}</span>
            <span class="text-cds-text-secondary">{{ transaction.producer_phone }}</span>
          </div>

          <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
            <span class="text-cds-text-helper block mb-1">Collecteur (Repreneur)</span>
            <span class="font-bold text-cds-text-primary block">{{ transaction.collector_organization || 'Collecteur' }}</span>
            <span class="text-cds-text-secondary">{{ transaction.collector_phone }}</span>
          </div>

          <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
            <span class="text-cds-text-helper block mb-1">Séquestre / Escrow</span>
            <span class="font-mono text-cds-link-primary font-bold block">{{ transaction.escrow_reference || 'En attente' }}</span>
            <span class="text-cds-text-secondary">
              Total : {{ transaction.total_amount ? formatMoney(transaction.total_amount) : 'À peser' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Action Area depending on role and status -->

      <!-- 1. PRODUCER VIEW: QR Code Display for Field Collector to scan -->
      <div
        v-if="transaction.viewer_role === 'producer' && transaction.payment_status === 'escrow_locked'"
        class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8"
      >
        <div class="text-center max-w-md mx-auto">
          <h2 class="text-lg font-bold text-cds-text-primary">Présenter ce QR Code au collecteur</h2>
          <p class="text-xs text-cds-text-helper mt-1 mb-6">
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
        class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8"
      >
        <div class="max-w-md mx-auto text-center space-y-4">
          <div class="flex items-center justify-center text-cds-support-info">
            <Lineicons :icon="Icons.weighing" :size="32" color="currentColor" />
          </div>
          <h2 class="text-lg font-bold text-cds-text-primary">Pesée enregistrée par le collecteur</h2>
          <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle text-left space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-cds-text-secondary">Poids constaté :</span>
              <span class="font-bold text-cds-text-primary">{{ formatQuantity(transaction.final_weight, transaction.unit) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-cds-text-secondary">Montant net à débloquer :</span>
              <span class="font-bold text-cds-link-primary">{{ formatMoney(transaction.total_amount) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-cds-text-secondary">CO₂ évité estimé :</span>
              <span class="font-bold text-cds-link-primary">{{ formatCo2(transaction.co2_saved_total) }}</span>
            </div>
          </div>

          <div v-if="transaction.weighing_proof_url" class="mt-3">
            <span class="text-xs text-cds-text-secondary block mb-1">Preuve de pesée (balance / ticket) :</span>
            <img :src="transaction.weighing_proof_url" class="w-32 h-32 object-cover mx-auto border border-cds-border-subtle" />
          </div>

          <div class="flex space-x-3 pt-2">
            <button
              @click="openDisputeModal = true"
              type="button"
              class="cds--btn cds--btn--secondary flex-1 justify-center"
            >
              Signaler un litige
            </button>
            <button
              @click="confirmCollection"
              :disabled="actionLoading"
              type="button"
              class="cds--btn cds--btn--primary flex-1 justify-center"
            >
              {{ actionLoading ? 'Déblocage...' : 'Valider & Débloquer fonds' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 3. COLLECTOR VIEW: Scanner QR & Saisie de pesée -->
      <div
        v-if="transaction.viewer_role === 'collector' && transaction.payment_status === 'escrow_locked'"
        class="bg-cds-layer-01 border border-cds-border-subtle p-6 sm:p-8 space-y-6"
      >
        <h2 class="text-lg font-bold text-cds-text-primary text-center">Étape terrain : Scan & Pesée</h2>

        <!-- Tab between Camera Scan & Manual Token -->
        <div class="max-w-md mx-auto space-y-6">
          <div v-if="!scannedToken" class="space-y-4">
            <ClientOnly>
              <QrScanner @scan="handleScanResult" />
            </ClientOnly>

            <div class="text-center">
              <span class="text-xs text-cds-text-helper">ou saisie manuelle du token de sécurité</span>
              <div class="mt-2 flex gap-2">
                <input
                  v-model="manualToken"
                  type="text"
                  placeholder="Collez le token du QR code..."
                  class="cds--text-input font-mono"
                />
                <button
                  @click="scannedToken = manualToken"
                  type="button"
                  class="cds--btn cds--btn--secondary shrink-0"
                >
                  OK
                </button>
              </div>
            </div>
          </div>

          <!-- Once token verified / scanned, show weighing form -->
          <div v-else class="p-6 bg-cds-layer-02 border border-cds-border-interactive space-y-4">
            <div class="flex items-center space-x-2 text-cds-support-success text-xs font-semibold">
              <Lineicons :icon="Icons.success" :size="16" color="currentColor" />
              <span>QR code validé avec succès</span>
            </div>

            <div class="cds--form-item">
              <label class="cds--label" for="weighing-final-weight">
                Poids réel constaté sur la balance ({{ transaction.unit }})
              </label>
              <input
                id="weighing-final-weight"
                v-model.number="weighingForm.final_weight"
                type="number"
                step="0.01"
                min="0.1"
                required
                class="cds--text-input font-mono font-bold"
              />
            </div>

            <!-- Weighing proof photo -->
            <div class="cds--form-item">
              <label class="cds--label" for="weighing-proof">
                Photo justificative (ticket ou affichage balance)
              </label>
              <input
                id="weighing-proof"
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
                class="cds--btn cds--btn--tertiary cds--btn--full justify-center"
              >
                {{ uploadingProof ? 'Téléversement en cours...' : (weighingForm.weighing_proof_url ? '✓ Photo ajoutée (changer)' : '+ Prendre une photo du ticket') }}
              </button>
            </div>

            <button
              @click="submitWeighing"
              :disabled="actionLoading"
              type="button"
              class="cds--btn cds--btn--primary cds--btn--full justify-center"
            >
              {{ actionLoading ? 'Enregistrement...' : 'Enregistrer la pesée contradictoire' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Dispute Modal -->
    <div
      v-if="openDisputeModal"
      class="cds--modal cds--modal--enable-presence"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dispute-modal-heading"
    >
      <div class="cds--modal-container">
        <header class="cds--modal-header">
          <h2 id="dispute-modal-heading" class="cds--modal-header__heading">Ouvrir un litige</h2>
          <button
            class="cds--modal-close"
            type="button"
            aria-label="Fermer"
            @click="openDisputeModal = false"
          >
            <Lineicons class="cds--modal-close__icon" :icon="Icons.close" :size="20" color="currentColor" />
          </button>
        </header>

        <div class="cds--modal-content">
          <p class="text-xs text-cds-text-helper">Expliquez le problème pour arbitrage par un administrateur.</p>

          <textarea
            v-model="disputeReason"
            rows="4"
            required
            placeholder="Ex: Écart de poids injustifié, matière non conforme..."
            class="cds--text-area mt-4"
          ></textarea>
        </div>

        <footer class="cds--modal-footer">
          <button
            @click="openDisputeModal = false"
            type="button"
            class="cds--btn cds--btn--secondary"
          >
            Annuler
          </button>
          <button
            @click="submitDispute"
            :disabled="actionLoading || !disputeReason"
            type="button"
            class="cds--btn cds--btn--danger"
          >
            Déclarer le litige
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { Transaction } from '~/types'
import { transactionStatusLabel, transactionStatusBadgeClass } from '~/utils/labels'

const route = useRoute()
const txId = route.params.id as string
const { apiFetch } = useApi()
// Les NUMERIC de l'API arrivent en chaîne : le formatage passe par useFormat
const { formatMoney, formatQuantity, formatCo2 } = useFormat()

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


onMounted(() => {
  fetchTransaction()
})
</script>
