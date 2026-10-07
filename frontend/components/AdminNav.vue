<template>
  <!--
    Onglets du back-office. Reste collé sous l'en-tête applicatif (h-16 côté layout).
    Style Carbon : surface layer-01, séparateur subtil, indicateur d'onglet actif
    porté par une bordure interactive plutôt qu'une pastille colorée.
  -->
  <div class="border-b border-cds-border-subtle bg-cds-layer-01 sticky top-16 z-30">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <nav class="flex items-center overflow-x-auto" aria-label="Navigation administration">
        <NuxtLink
          v-for="item in items"
          :key="item.to"
          :to="item.to"
          class="shrink-0 px-4 py-3 text-xs font-medium transition-colors flex items-center space-x-2 border-b-2 -mb-px"
          :class="isActive(item.to)
            ? 'text-cds-text-primary border-cds-border-interactive'
            : 'text-cds-text-secondary border-transparent hover:text-cds-text-primary hover:bg-cds-layer-hover-01'"
        >
          <span>{{ item.label }}</span>
          <span
            v-if="item.to === '/admin/disputes' && disputeCount"
            class="cds--tag cds--tag--red"
          >
            {{ disputeCount }}
          </span>
        </NuxtLink>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    /** Nombre de litiges ouverts, affiché en pastille sur l'onglet Litiges. */
    disputeCount?: number
  }>(),
  { disputeCount: 0 }
)

const route = useRoute()

const items = [
  { to: '/admin', label: "Vue d'ensemble" },
  { to: '/admin/transactions', label: 'Transactions' },
  { to: '/admin/disputes', label: 'Litiges' },
  { to: '/admin/users', label: 'Utilisateurs' },
  { to: '/admin/categories', label: 'Catégories' }
]

const isActive = (to: string): boolean =>
  to === '/admin' ? route.path === '/admin' : route.path.startsWith(to)
</script>
