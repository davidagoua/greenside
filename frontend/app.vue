<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
const { themeClass } = useTheme()

/**
 * La classe de thème Carbon est posée sur <html> et rendue côté serveur à partir
 * du cookie : le premier pixel est déjà dans le bon thème (aucun flash).
 */
useHead({
  htmlAttrs: {
    lang: 'fr',
    class: themeClass
  }
})
</script>
