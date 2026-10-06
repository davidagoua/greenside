<template>
  <div class="relative w-full overflow-hidden rounded-2xl bg-slate-900 border border-slate-800">
    <!-- Camera Video Element -->
    <div id="reader" class="w-full"></div>

    <!-- Scanner Overlay & Controls -->
    <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="inline-block w-2.5 h-2.5 rounded-full" :class="isScanning ? 'bg-eco-500 animate-ping' : 'bg-slate-500'"></span>
        <span class="text-xs font-medium text-slate-300">
          {{ isScanning ? 'Caméra active : Visez le QR code du producteur' : 'Scanner en pause' }}
        </span>
      </div>

      <button
        v-if="!isScanning"
        @click="startScanning"
        type="button"
        class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-eco-600 text-white hover:bg-eco-500 transition"
      >
        Démarrer caméra
      </button>
      <button
        v-else
        @click="stopScanning"
        type="button"
        class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
      >
        Arrêter
      </button>
    </div>

    <div v-if="errorMessage" class="p-3 text-xs bg-red-950/60 border-t border-red-800/40 text-red-300">
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
    await html5QrCode.start(
      { facingMode: 'environment' },
      config,
      qrCodeSuccessCallback,
      () => {}
    )
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
    } catch (e) {
      // ignore clean-up errors
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
