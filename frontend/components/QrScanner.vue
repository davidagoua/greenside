<template>
  <div class="relative w-full overflow-hidden bg-cds-layer-01 border border-cds-border-subtle">
    <!-- Flux caméra (conteneur géré par html5-qrcode) -->
    <div id="reader" class="w-full"></div>

    <!-- État et commandes -->
    <div class="p-4 bg-cds-layer-02 border-t border-cds-border-subtle flex items-center justify-between gap-4">
      <div class="flex items-center space-x-2 min-w-0">
        <span
          class="inline-block w-2.5 h-2.5 shrink-0 rounded-full"
          :class="isScanning ? 'bg-cds-support-success animate-ping' : 'bg-cds-text-disabled'"
        ></span>
        <span class="text-xs text-cds-text-secondary truncate">
          {{ isScanning ? 'Caméra active : visez le QR code du producteur' : 'Scanner en pause' }}
        </span>
      </div>

      <button
        v-if="!isScanning"
        type="button"
        class="cds--btn cds--btn--primary cds--btn--sm shrink-0"
        @click="startScanning"
      >
        Démarrer la caméra
      </button>
      <button
        v-else
        type="button"
        class="cds--btn cds--btn--ghost cds--btn--sm shrink-0"
        @click="stopScanning"
      >
        Arrêter
      </button>
    </div>

    <div
      v-if="errorMessage"
      class="p-3 text-xs bg-cds-layer-01 border-t border-cds-border-subtle border-l-2 border-l-cds-support-error text-cds-support-error"
      role="alert"
    >
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits<{
  (e: 'scan', result: string): void
}>()

const isScanning = ref(false)
const errorMessage = ref('')
let html5QrCode: any = null

const startScanning = async () => {
  errorMessage.value = ''
  try {
    const { Html5Qrcode } = await import('html5-qrcode')
    if (!html5QrCode) {
      html5QrCode = new Html5Qrcode('reader')
    }

    const qrCodeSuccessCallback = (decodedText: string) => {
      stopScanning()
      emit('scan', decodedText)
    }

    const config = { fps: 10, qrbox: { width: 250, height: 250 } }
    await html5QrCode.start({ facingMode: 'environment' }, config, qrCodeSuccessCallback, () => {})
    isScanning.value = true
  } catch (err: any) {
    errorMessage.value = "Impossible d'accéder à la caméra : " + (err.message || 'Permission refusée')
    isScanning.value = false
  }
}

const stopScanning = async () => {
  if (html5QrCode && isScanning.value) {
    try {
      await html5QrCode.stop()
    } catch {
      // erreurs de nettoyage ignorées volontairement
    }
    isScanning.value = false
  }
}

onMounted(() => {
  startScanning()
})

onBeforeUnmount(() => {
  stopScanning()
})
</script>
