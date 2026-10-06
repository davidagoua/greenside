<template>
  <div class="min-h-[85vh] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-slate-950/80">
      <!-- Tabs Switcher -->
      <div class="flex rounded-xl bg-slate-950 p-1 mb-8 border border-slate-800">
        <button
          @click="mode = 'login'"
          type="button"
          class="flex-1 py-2 text-xs font-semibold rounded-lg transition"
          :class="mode === 'login' ? 'bg-eco-600 text-white shadow' : 'text-slate-400 hover:text-white'"
        >
          Connexion
        </button>
        <button
          @click="mode = 'register'"
          type="button"
          class="flex-1 py-2 text-xs font-semibold rounded-lg transition"
          :class="mode === 'register' ? 'bg-eco-600 text-white shadow' : 'text-slate-400 hover:text-white'"
        >
          Inscription
        </button>
      </div>

      <div class="text-center mb-6">
        <h1 class="text-2xl font-bold text-white tracking-tight">
          {{ mode === 'login' ? 'Bon retour sur EcoLoop' : 'Créer un compte' }}
        </h1>
        <p class="text-xs text-slate-400 mt-1">
          {{ mode === 'login' ? 'Connectez-vous pour accéder à vos transactions' : 'Rejoignez la chaîne de valorisation circulaire' }}
        </p>
      </div>

      <!-- Error banner -->
      <div v-if="error" class="mb-5 p-3 rounded-xl bg-red-950/80 border border-red-800 text-red-200 text-xs flex items-center space-x-2">
        <svg class="w-4 h-4 shrink-0 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Email professionnel</label>
          <input
            v-model="form.email"
            type="email"
            required
            placeholder="contact@entreprise.com"
            class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-eco-500 text-sm transition"
          />
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Mot de passe</label>
          <input
            v-model="form.password"
            type="password"
            required
            placeholder="Min. 8 caractères, 1 chiffre"
            class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-eco-500 text-sm transition"
          />
        </div>

        <template v-if="mode === 'register'">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Votre rôle principal</label>
            <div class="grid grid-cols-2 gap-3">
              <label
                class="flex flex-col items-center justify-center p-3 rounded-xl border cursor-pointer transition text-center"
                :class="form.role === 'producer' ? 'bg-eco-950/60 border-eco-500 text-eco-300' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'"
              >
                <input type="radio" value="producer" v-model="form.role" class="sr-only" />
                <span class="text-sm font-bold">Producteur</span>
                <span class="text-[10px] text-slate-400 mt-0.5">Je génère des déchets</span>
              </label>

              <label
                class="flex flex-col items-center justify-center p-3 rounded-xl border cursor-pointer transition text-center"
                :class="form.role === 'collector' ? 'bg-eco-950/60 border-eco-500 text-eco-300' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'"
              >
                <input type="radio" value="collector" v-model="form.role" class="sr-only" />
                <span class="text-sm font-bold">Collecteur</span>
                <span class="text-[10px] text-slate-400 mt-0.5">Je collecte & valorise</span>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Nom de l'organisation / Entreprise</label>
            <input
              v-model="form.organization_name"
              type="text"
              placeholder="Ex: Plastique Recyclage SA"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-eco-500 text-sm transition"
            />
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Numéro de téléphone (avec indicatif)</label>
            <input
              v-model="form.phone"
              type="tel"
              required
              placeholder="+221 77 123 45 67"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-eco-500 text-sm transition"
            />
          </div>
        </template>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 px-4 rounded-xl font-semibold text-white bg-eco-600 hover:bg-eco-500 shadow-lg shadow-eco-600/30 transition disabled:opacity-50 flex items-center justify-center space-x-2 text-sm mt-6"
        >
          <span v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <span>{{ mode === 'login' ? 'Se connecter' : "S'inscrire" }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

const form = reactive({
  email: '',
  password: '',
  role: 'producer' as 'producer' | 'collector',
  organization_name: '',
  phone: ''
})

const { setAuth } = useAuth()
const config = useRuntimeConfig()

const handleSubmit = async () => {
  loading.value = true
  error.value = ''

  try {
    const endpoint = mode.value === 'login' ? '/auth/login' : '/auth/register'
    const payload = mode.value === 'login'
      ? { email: form.email, password: form.password }
      : {
          email: form.email,
          password: form.password,
          role: form.role,
          organization_name: form.organization_name || null,
          phone: form.phone
        }

    const res = await $fetch<any>(`${config.public.apiBaseUrl}${endpoint}`, {
      method: 'POST',
      body: payload
    })

    setAuth(res.access_token, res.user)
    navigateTo('/marketplace')
  } catch (err: any) {
    error.value = err.response?._data?.detail || err.message || 'Une erreur est survenue'
  } finally {
    loading.value = false
  }
}
</script>
