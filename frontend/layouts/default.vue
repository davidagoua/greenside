<template>
  <div class="min-h-screen bg-cds-background flex flex-col">
    <!-- En-tête -->
    <header class="sticky top-0 z-40 bg-cds-layer-01 border-b border-cds-border-subtle">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        <!-- Marque -->
        <NuxtLink to="/marketplace" class="flex items-center space-x-3 shrink-0">
          <span class="w-9 h-9 bg-cds-background-brand flex items-center justify-center">
            <Lineicons :icon="Icons.brand" :size="22" color="var(--cds-icon-on-color)" />
          </span>
          <span class="flex items-center space-x-2">
            <span class="text-base font-semibold text-cds-text-primary tracking-tight">EcoLoop</span>
            <span class="cds--tag cds--tag--gray hidden sm:inline-flex">B2B/B2C</span>
          </span>
        </NuxtLink>

        <!-- Navigation principale -->
        <nav class="hidden md:flex items-center" aria-label="Navigation principale">
          <NuxtLink
            to="/marketplace"
            class="px-3 py-2 text-sm transition-colors"
            :class="navClass('/marketplace')"
          >
            Marketplace
          </NuxtLink>

          <NuxtLink
            v-if="user?.role === 'producer'"
            to="/listings/new"
            class="px-3 py-2 text-sm transition-colors"
            :class="navClass('/listings/new')"
          >
            Déposer une annonce
          </NuxtLink>

          <NuxtLink
            v-if="user && user.role !== 'admin'"
            to="/dashboard/impact"
            class="px-3 py-2 text-sm transition-colors"
            :class="navClass('/dashboard/impact')"
          >
            Impact RSE
          </NuxtLink>

          <NuxtLink
            v-if="user?.role === 'admin'"
            to="/admin"
            class="px-3 py-2 text-sm transition-colors"
            :class="navClass('/admin')"
          >
            Administration
          </NuxtLink>
        </nav>

        <!-- Actions -->
        <div class="flex items-center space-x-2 shrink-0">
          <!-- Sélecteur de thème -->
          <button
            type="button"
            class="cds--btn cds--btn--ghost cds--btn--sm"
            :title="isDark ? 'Passer au thème clair' : 'Passer au thème sombre'"
            :aria-label="isDark ? 'Passer au thème clair' : 'Passer au thème sombre'"
            @click="toggleTheme"
          >
            <Lineicons
              :icon="isDark ? Icons.themeLight : Icons.themeDark"
              :size="18"
              color="currentColor"
            />
            <span class="hidden lg:inline ml-2">{{ isDark ? 'Clair' : 'Sombre' }}</span>
          </button>

          <template v-if="user">
            <div class="hidden sm:flex flex-col text-right leading-tight">
              <span class="text-xs font-medium text-cds-text-primary truncate max-w-[12rem]">
                {{ user.organization_name || user.email }}
              </span>
              <span class="text-[11px] text-cds-text-secondary">{{ roleLabel(user.role) }}</span>
            </div>
            <button
              type="button"
              class="cds--btn cds--btn--ghost cds--btn--sm"
              title="Déconnexion"
              aria-label="Déconnexion"
              @click="logout"
            >
              <Lineicons :icon="Icons.logout" :size="18" color="currentColor" />
            </button>
          </template>

          <NuxtLink v-else to="/auth" class="cds--btn cds--btn--primary cds--btn--sm">
            Connexion
          </NuxtLink>
        </div>
      </div>
    </header>

    <!-- Contenu -->
    <main class="flex-1 pb-20 md:pb-8">
      <slot />
    </main>

    <!-- Navigation basse (mobile) -->
    <nav
      class="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-cds-layer-01 border-t border-cds-border-subtle"
      aria-label="Navigation mobile"
    >
      <div class="grid grid-flow-col auto-cols-fr">
        <NuxtLink v-for="tab in tabs" :key="tab.to" :to="tab.to" class="eco-tab" :class="tabClass(tab.to)">
          <Lineicons :icon="tab.icon" :size="22" color="currentColor" />
          <span class="text-[10px] mt-1">{{ tab.label }}</span>
        </NuxtLink>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'
import { roleLabel } from '~/utils/labels'

const route = useRoute()
const { user, logout, fetchCurrentUser } = useAuth()
const { isDark, toggleTheme } = useTheme()

/**
 * Entrées de la barre mobile. Le nombre d'onglets dépend du rôle : la grille
 * s'adapte (auto-cols-fr) au lieu de réserver des colonnes vides.
 */
const tabs = computed(() => {
  const items: Array<{ to: string; icon: (typeof Icons)[keyof typeof Icons]; label: string }> = [
    { to: '/marketplace', icon: Icons.map, label: 'Carte' }
  ]

  if (user.value?.role === 'producer') {
    items.push({ to: '/listings/new', icon: Icons.add, label: 'Déposer' })
  }

  if (user.value?.role === 'admin') {
    items.push({ to: '/admin', icon: Icons.admin, label: 'Admin' })
  } else {
    items.push({ to: '/dashboard/impact', icon: Icons.chart, label: 'Impact' })
  }

  items.push({ to: '/auth', icon: Icons.account, label: 'Compte' })
  return items
})

/** Lien de navigation actif : surface sélectionnée Carbon. */
const navClass = (path: string) =>
  route.path === path || route.path.startsWith(path + '/')
    ? 'text-cds-text-primary border-b-2 border-cds-border-interactive'
    : 'text-cds-text-secondary hover:text-cds-text-primary hover:bg-cds-layer-hover-01'

const tabClass = (path: string) =>
  route.path === path || route.path.startsWith(path + '/')
    ? 'text-cds-link-primary border-t-2 border-cds-border-interactive'
    : 'text-cds-text-secondary border-t-2 border-transparent'

onMounted(() => {
  // Le middleware (ex. garde admin) a pu déjà résoudre la session : on évite
  // un second appel à /auth/me à chaque navigation.
  if (!user.value) fetchCurrentUser()
})
</script>
