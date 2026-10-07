<template>
  <div>
    <AdminNav :dispute-count="disputes.length" />

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- En-tête de page -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">Litiges à arbitrer</h1>
          <p class="text-xs text-cds-text-helper mt-1">
            Les fonds restent séquestrés jusqu'à la décision de l'administrateur
          </p>
        </div>
        <button
          type="button"
          :disabled="loading"
          class="cds--btn cds--btn--secondary cds--btn--sm self-start"
          @click="fetchDisputes"
        >
          <span v-if="loading" class="eco-spinner w-5 h-5 mr-2"></span>
          {{ loading ? 'Chargement…' : 'Rafraîchir' }}
        </button>
      </div>

      <!-- Bandeau d'erreur -->
      <div
        v-if="error"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error text-cds-support-error text-xs flex items-start justify-between gap-4"
      >
        <span>{{ error }}</span>
        <button
          type="button"
          class="cds--btn cds--btn--danger--ghost cds--btn--sm shrink-0"
          @click="fetchDisputes"
        >
          Réessayer
        </button>
      </div>

      <!-- Bandeau de succès -->
      <div
        v-if="successMessage"
        class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-success text-cds-text-primary text-xs flex items-start justify-between gap-4"
      >
        <span>{{ successMessage }}</span>
        <button
          type="button"
          class="cds--btn cds--btn--ghost cds--btn--sm shrink-0"
          @click="successMessage = ''"
        >
          Fermer
        </button>
      </div>

      <div v-if="loading && !disputes.length" class="space-y-4">
        <div
          v-for="i in 2"
          :key="i"
          class="h-48 bg-cds-layer-01 border border-cds-border-subtle animate-pulse"
        ></div>
      </div>

      <!-- État vide -->
      <div
        v-else-if="!disputes.length"
        class="p-12 text-center bg-cds-layer-01 border border-cds-border-subtle"
      >
        <div class="w-12 h-12 mx-auto bg-cds-layer-02 flex items-center justify-center">
          <Lineicons :icon="Icons.success" :size="24" color="var(--cds-support-success)" />
        </div>
        <p class="mt-4 text-sm font-semibold text-cds-text-primary">Aucun litige ouvert</p>
        <p class="mt-1 text-xs text-cds-text-helper">Toutes les transactions se déroulent normalement.</p>
      </div>

      <!-- Cartes de litige -->
      <div v-else class="space-y-4">
        <article
          v-for="tx in disputes"
          :key="tx.id"
          class="bg-cds-layer-01 border border-cds-support-error p-6 space-y-5"
        >
          <header class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-5 border-b border-cds-border-subtle">
            <div class="min-w-0">
              <div class="flex items-center flex-wrap gap-2">
                <span class="text-xs font-mono text-cds-text-helper">#{{ tx.id.substring(0, 8) }}</span>
                <span class="cds--tag" :class="transactionStatusBadgeClass(tx.payment_status)">
                  {{ transactionStatusLabel(tx.payment_status) }}
                </span>
                <span class="text-[10px] text-cds-text-helper">ouvert le {{ formatDateTime(tx.updated_at || tx.created_at) }}</span>
              </div>
              <h2 class="text-lg font-bold text-cds-text-primary mt-1.5 truncate">{{ tx.listing_title }}</h2>
              <p class="text-xs text-cds-text-secondary mt-1">
                {{ tx.category_name }} · 📍 {{ tx.address_text }}
              </p>
            </div>

            <div class="flex gap-2 shrink-0">
              <NuxtLink
                :to="`/transactions/${tx.id}`"
                class="cds--btn cds--btn--secondary cds--btn--sm"
              >
                Inspecter
                <Lineicons class="ml-2" :icon="Icons.next" :size="16" color="currentColor" />
              </NuxtLink>
              <button
                type="button"
                class="cds--btn cds--btn--danger"
                @click="openResolveModal(tx)"
              >
                Arbitrer
              </button>
            </div>
          </header>

          <!-- Motif invoqué -->
          <div class="p-4 bg-cds-layer-01 border-l-2 border-cds-support-error">
            <span class="text-[10px] font-semibold text-cds-support-error uppercase tracking-wider">Motif invoqué</span>
            <p class="text-xs text-cds-text-secondary mt-1.5 whitespace-pre-line">{{ tx.dispute_reason || 'Non précisé' }}</p>
          </div>

          <!-- Détails -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
              <span class="text-cds-text-helper block mb-1">Producteur (remettant)</span>
              <span class="font-bold text-cds-text-primary block truncate">{{ tx.producer_organization || 'Producteur particulier' }}</span>
              <span class="text-cds-text-secondary">{{ tx.producer_phone || '—' }}</span>
            </div>

            <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
              <span class="text-cds-text-helper block mb-1">Collecteur (repreneur)</span>
              <span class="font-bold text-cds-text-primary block truncate">{{ tx.collector_organization || 'Collecteur' }}</span>
              <span class="text-cds-text-secondary">{{ tx.collector_phone || '—' }}</span>
            </div>

            <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
              <span class="text-cds-text-helper block mb-1">Montant séquestré</span>
              <span class="font-mono font-bold text-cds-support-warning block">{{ formatMoney(tx.total_amount) }}</span>
              <span class="text-[10px] font-mono text-cds-text-helper">{{ tx.escrow_reference || 'sans référence' }}</span>
            </div>

            <div class="p-4 bg-cds-layer-02 border border-cds-border-subtle">
              <span class="text-cds-text-helper block mb-1">Pesée contradictoire</span>
              <span
                class="font-mono font-bold block"
                :class="tx.final_weight ? 'text-cds-support-info' : 'text-cds-text-helper'"
              >
                {{ tx.final_weight ? formatQuantity(tx.final_weight, tx.unit) : 'Non réalisée' }}
              </span>
              <span class="text-[10px] text-cds-text-helper">
                prévu {{ tx.agreed_quantity ? formatQuantity(tx.agreed_quantity, tx.unit) : '—' }}
              </span>
            </div>
          </div>

          <!-- Traçabilité -->
          <div class="flex flex-wrap gap-x-6 gap-y-2 text-[10px] text-cds-text-helper">
            <span>Réservée : <b class="text-cds-text-secondary">{{ formatDateTime(tx.created_at) }}</b></span>
            <span>QR scanné : <b class="text-cds-text-secondary">{{ tx.qr_scanned_at ? formatDateTime(tx.qr_scanned_at) : 'jamais' }}</b></span>
            <span>Pesée : <b class="text-cds-text-secondary">{{ tx.collected_at ? formatDateTime(tx.collected_at) : 'jamais' }}</b></span>
            <span v-if="tx.bsdd_number">BSDD : <b class="font-mono text-cds-text-secondary">{{ tx.bsdd_number }}</b></span>
            <span v-if="tx.weighing_proof_url">
              <a
                :href="tx.weighing_proof_url"
                target="_blank"
                rel="noopener"
                class="text-cds-link-primary hover:text-cds-link-primary-hover font-semibold"
              >
                Ticket de pesée ↗
              </a>
            </span>
          </div>
        </article>
      </div>
    </div>

    <!-- Modale d'arbitrage -->
    <div
      v-if="selected"
      class="cds--modal cds--modal--enable-presence"
      role="dialog"
      aria-modal="true"
      aria-labelledby="resolve-modal-title"
      @click.self="closeResolveModal"
    >
      <div
        ref="modalRef"
        tabindex="-1"
        class="cds--modal-container focus:outline-none"
        @keydown.esc="closeResolveModal"
      >
        <header class="cds--modal-header flex items-start justify-between gap-4">
          <h2 id="resolve-modal-title" class="cds--modal-header__heading">Arbitrer le litige</h2>
          <button class="cds--modal-close" type="button" aria-label="Fermer" @click="closeResolveModal">
            <Lineicons class="cds--modal-close__icon" :icon="Icons.close" :size="20" color="currentColor" />
          </button>
        </header>

        <div class="cds--modal-content">
          <p class="text-xs text-cds-text-helper">
            Transaction <span class="font-mono">#{{ selected.id.substring(0, 8) }}</span> —
            {{ selected.listing_title }}
          </p>

          <fieldset class="mt-5 space-y-3" :disabled="submitting">
            <legend class="sr-only">Décision d'arbitrage</legend>

            <label
              class="block p-4 border cursor-pointer transition"
              :class="[
                resolution === 'paid'
                  ? 'border-cds-border-interactive bg-cds-layer-02'
                  : 'border-cds-border-subtle bg-cds-field hover:border-cds-border-strong',
                canPay ? '' : 'opacity-50 cursor-not-allowed'
              ]"
            >
              <span class="flex items-start space-x-3">
                <input
                  v-model="resolution"
                  type="radio"
                  value="paid"
                  :disabled="!canPay"
                  class="mt-0.5 accent-cds-interactive"
                />
                <span>
                  <span class="block text-sm font-bold text-cds-text-primary">Libérer les fonds au producteur</span>
                  <span class="block text-[11px] text-cds-text-secondary mt-1">
                    Le séquestre est débloqué, la transaction passe en « payé » et le lot est clôturé.
                    Le bordereau BSDD reste valable.
                  </span>
                  <span v-if="!canPay" class="block text-[11px] text-cds-support-error mt-1.5 font-semibold">
                    Impossible : aucune pesée n'a été enregistrée sur cette transaction.
                  </span>
                </span>
              </span>
            </label>

            <label
              class="block p-4 border cursor-pointer transition"
              :class="resolution === 'cancelled'
                ? 'border-cds-support-error bg-cds-layer-02'
                : 'border-cds-border-subtle bg-cds-field hover:border-cds-border-strong'"
            >
              <span class="flex items-start space-x-3">
                <input
                  v-model="resolution"
                  type="radio"
                  value="cancelled"
                  class="mt-0.5 accent-cds-support-error"
                />
                <span>
                  <span class="block text-sm font-bold text-cds-text-primary">Annuler et rembourser</span>
                  <span class="block text-[11px] text-cds-text-secondary mt-1">
                    Le séquestre est restitué au collecteur et l'annonce repasse en « publiée » pour être
                    proposée à nouveau sur la marketplace.
                  </span>
                </span>
              </span>
            </label>
          </fieldset>

          <div class="cds--form-item mt-5">
            <label class="cds--label" for="resolution-note">
              Note de résolution (facultative)
            </label>
            <textarea
              id="resolution-note"
              v-model="note"
              rows="3"
              maxlength="2000"
              :disabled="submitting"
              placeholder="Motivation de la décision, éléments constatés, accord des parties…"
              class="cds--text-area"
            ></textarea>
            <span class="block mt-1 text-[10px] text-cds-text-helper">{{ note.length }} / 2000</span>
          </div>

          <p
            v-if="modalError"
            class="mt-4 p-3 bg-cds-layer-01 border-l-2 border-cds-support-error text-cds-support-error text-xs"
          >
            {{ modalError }}
          </p>
        </div>

        <footer class="cds--modal-footer">
          <button
            type="button"
            :disabled="submitting"
            class="cds--btn cds--btn--secondary"
            @click="closeResolveModal"
          >
            Annuler
          </button>
          <button
            type="button"
            :disabled="submitting"
            class="cds--btn"
            :class="resolution === 'paid' ? 'cds--btn--primary' : 'cds--btn--danger'"
            @click="submitResolution"
          >
            {{ submitting ? 'Traitement…' : resolution === 'paid' ? 'Libérer les fonds' : 'Rembourser & annuler' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import type { Transaction, ResolveDisputeInput } from '~/types'
import { transactionStatusLabel, transactionStatusBadgeClass } from '~/utils/labels'

definePageMeta({ middleware: 'admin' })

useHead({ title: 'Litiges — Administration EcoLoop' })

const { apiFetch } = useApi()
const { formatMoney, formatQuantity, formatDateTime, errorMessage } = useFormat()

const disputes = ref<Transaction[]>([])
const loading = ref(true)
const error = ref('')
const successMessage = ref('')

const selected = ref<Transaction | null>(null)
const resolution = ref<'paid' | 'cancelled'>('cancelled')
const note = ref('')
const submitting = ref(false)
const modalError = ref('')
const modalRef = ref<HTMLElement | null>(null)

/**
 * Le backend refuse une clôture « payé » sans pesée enregistrée
 * (`NO_WEIGHING`) : on désactive l'option en amont plutôt que de laisser
 * l'administrateur découvrir l'erreur après soumission.
 */
const canPay = computed(() => selected.value?.final_weight != null)

const fetchDisputes = async () => {
  loading.value = true
  error.value = ''
  try {
    disputes.value = await apiFetch<Transaction[]>('/admin/disputes')
  } catch (err) {
    disputes.value = []
    error.value = errorMessage(err, 'Impossible de charger les litiges')
  } finally {
    loading.value = false
  }
}

const openResolveModal = async (tx: Transaction) => {
  selected.value = tx
  note.value = ''
  modalError.value = ''
  resolution.value = tx.final_weight != null ? 'paid' : 'cancelled'
  await nextTick()
  modalRef.value?.focus()
}

const closeResolveModal = () => {
  if (submitting.value) return
  selected.value = null
  modalError.value = ''
}

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && selected.value) closeResolveModal()
}

const submitResolution = async () => {
  if (!selected.value) return
  submitting.value = true
  modalError.value = ''
  try {
    const payload: ResolveDisputeInput = {
      resolution: resolution.value,
      note: note.value.trim() || null
    }
    await apiFetch(`/admin/transactions/${selected.value.id}/resolve`, {
      method: 'POST',
      body: payload
    })
    successMessage.value =
      resolution.value === 'paid'
        ? 'Litige arbitré : les fonds ont été libérés au profit du producteur.'
        : 'Litige arbitré : les fonds ont été remboursés et le lot republié.'
    selected.value = null
    await fetchDisputes()
  } catch (err) {
    modalError.value = errorMessage(err, "Échec de l'arbitrage")
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchDisputes()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
