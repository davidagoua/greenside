<template>
  <div class="flex flex-col items-center justify-center p-6 bg-cds-layer-01 border border-cds-border-subtle">
    <div v-if="loading" class="w-64 h-64 flex items-center justify-center">
      <span class="eco-spinner w-8 h-8"></span>
    </div>

    <!--
      Le QR code conserve un fond blanc et un motif sombre quel que soit le thème :
      c'est une contrainte fonctionnelle de lisibilité optique pour le scanner.
      Une inversion des couleurs rendrait le code illisible par la caméra.
    -->
    <div v-else class="p-4 bg-white border border-cds-border-subtle">
      <canvas ref="canvasRef"></canvas>
    </div>

    <p class="mt-4 text-xs font-mono text-cds-text-helper text-center max-w-xs break-all">
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
  // Sans le passage de `loading` à false, la valeur absente laissait le
  // composant bloqué sur son indicateur de chargement.
  if (!props.value || !canvasRef.value) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const QRCode = (await import('qrcode')).default
    await QRCode.toCanvas(canvasRef.value, props.value, {
      width: 240,
      margin: 1,
      color: {
        dark: '#161616', // gray-100 Carbon
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

watch(
  () => [props.value, props.token],
  () => {
    generateQr()
  }
)
</script>
