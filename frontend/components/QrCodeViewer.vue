<template>
  <div class="flex flex-col items-center justify-center p-6 bg-slate-900 border border-slate-800 rounded-2xl">
    <div v-if="loading" class="w-64 h-64 flex items-center justify-center">
      <div class="w-8 h-8 border-4 border-eco-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else class="p-4 bg-white rounded-xl shadow-lg">
      <canvas ref="canvasRef"></canvas>
    </div>

    <p class="mt-4 text-xs font-mono text-slate-400 text-center max-w-xs break-all">
      Token : {{ token }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  value: string
  token: string
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const loading = ref(true)

const generateQr = async () => {
  if (!props.value || !canvasRef.value) return
  loading.value = true
  try {
    const QRCode = (await import('qrcode')).default
    await QRCode.toCanvas(canvasRef.value, props.value, {
      width: 240,
      margin: 1,
      color: {
        dark: '#0f172a',
        light: '#ffffff'
      }
    })
  } catch (err) {
    console.error('Erreur génération QR:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  generateQr()
})

watch(() => props.value, () => {
  generateQr()
})
</script>
