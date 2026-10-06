<template>
  <div class="min-h-screen bg-slate-950 flex flex-col">
    <!-- Top Navigation Header -->
    <header class="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <NuxtLink to="/marketplace" class="flex items-center space-x-3 group">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-eco-400 to-eco-600 flex items-center justify-center shadow-lg shadow-eco-500/20 group-hover:scale-105 transition">
            <svg class="w-6 h-6 text-slate-950 font-bold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <div>
            <span class="text-xl font-bold tracking-tight text-white flex items-center">
              Eco<span class="text-eco-400">Loop</span>
              <span class="ml-2 text-[10px] font-mono tracking-widest uppercase px-1.5 py-0.5 rounded bg-eco-950/80 border border-eco-500/30 text-eco-400">B2B/B2C</span>
            </span>
          </div>
        </NuxtLink>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <NuxtLink
            to="/marketplace"
            class="px-3.5 py-2 text-sm font-medium rounded-lg transition"
            :class="$route.path.startsWith('/marketplace') ? 'bg-slate-800 text-eco-400' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'"
          >
            Marketplace
          </NuxtLink>

          <NuxtLink
            v-if="user?.role === 'producer'"
            to="/listings/new"
            class="px-3.5 py-2 text-sm font-medium rounded-lg transition"
            :class="$route.path.startsWith('/listings/new') ? 'bg-slate-800 text-eco-400' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'"
          >
            + Déposer une annonce
          </NuxtLink>

          <NuxtLink
            to="/dashboard/impact"
            class="px-3.5 py-2 text-sm font-medium rounded-lg transition"
            :class="$route.path.startsWith('/dashboard/impact') ? 'bg-slate-800 text-eco-400' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'"
          >
            Impact RSE
          </NuxtLink>
        </nav>

        <!-- User Actions / Profile -->
        <div class="flex items-center space-x-3">
          <template v-if="user">
            <div class="hidden sm:flex flex-col text-right">
              <span class="text-xs font-semibold text-white">{{ user.organization_name || user.email }}</span>
              <span class="text-[11px] text-eco-400 capitalize">
                {{ user.role === 'producer' ? 'Producteur' : user.role === 'collector' ? 'Collecteur' : 'Admin' }}
              </span>
            </div>
            <button
              @click="logout"
              class="p-2 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 transition"
              title="Déconnexion"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </template>
          <template v-else>
            <NuxtLink
              to="/auth"
              class="px-4 py-2 text-sm font-medium rounded-xl bg-eco-600 text-white hover:bg-eco-500 shadow-md shadow-eco-600/20 transition"
            >
              Connexion
            </NuxtLink>
          </template>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 pb-20 md:pb-8">
      <slot />
    </main>

    <!-- Bottom Navigation Bar for Mobile PWA -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-lg border-t border-slate-800 px-6 py-2 flex justify-around">
      <NuxtLink to="/marketplace" class="flex flex-col items-center py-1 text-slate-400 hover:text-eco-400" :class="{ 'text-eco-400': $route.path === '/marketplace' }">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <span class="text-[10px] mt-0.5">Carte</span>
      </NuxtLink>

      <NuxtLink v-if="user?.role === 'producer'" to="/listings/new" class="flex flex-col items-center py-1 text-slate-400 hover:text-eco-400" :class="{ 'text-eco-400': $route.path === '/listings/new' }">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span class="text-[10px] mt-0.5">Déposer</span>
      </NuxtLink>

      <NuxtLink to="/dashboard/impact" class="flex flex-col items-center py-1 text-slate-400 hover:text-eco-400" :class="{ 'text-eco-400': $route.path === '/dashboard/impact' }">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span class="text-[10px] mt-0.5">Impact</span>
      </NuxtLink>

      <NuxtLink to="/auth" class="flex flex-col items-center py-1 text-slate-400 hover:text-eco-400" :class="{ 'text-eco-400': $route.path === '/auth' }">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="text-[10px] mt-0.5">Compte</span>
      </NuxtLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
const { user, logout, fetchCurrentUser } = useAuth()

onMounted(() => {
  fetchCurrentUser()
})
</script>
