<template>
  <div class="min-h-[85vh] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md bg-cds-layer-01 border border-cds-border-subtle p-8">
      <!-- Sélecteur de mode : contrôle segmenté, 100 % jetons Carbon -->
      <div
        class="flex bg-cds-layer-02 border border-cds-border-subtle mb-8"
        role="tablist"
        aria-label="Connexion ou inscription"
      >
        <button
          @click="mode = 'login'"
          type="button"
          role="tab"
          :aria-selected="mode === 'login'"
          class="flex-1 py-2 text-xs font-semibold border-b-2 transition-colors"
          :class="mode === 'login'
            ? 'bg-cds-background-selected border-cds-border-interactive text-cds-text-primary'
            : 'border-transparent text-cds-text-helper hover:bg-cds-layer-hover-01 hover:text-cds-text-primary'"
        >
          Connexion
        </button>
        <button
          @click="mode = 'register'"
          type="button"
          role="tab"
          :aria-selected="mode === 'register'"
          class="flex-1 py-2 text-xs font-semibold border-b-2 transition-colors"
          :class="mode === 'register'
            ? 'bg-cds-background-selected border-cds-border-interactive text-cds-text-primary'
            : 'border-transparent text-cds-text-helper hover:bg-cds-layer-hover-01 hover:text-cds-text-primary'"
        >
          Inscription
        </button>
      </div>

      <div class="text-center mb-6">
        <h1 class="text-2xl font-bold text-cds-text-primary tracking-tight">
          {{ mode === 'login' ? 'Bon retour sur EcoLoop' : 'Créer un compte' }}
        </h1>
        <p class="text-xs text-cds-text-helper mt-1">
          {{ mode === 'login' ? 'Connectez-vous pour accéder à vos transactions' : 'Rejoignez la chaîne de valorisation circulaire' }}
        </p>
      </div>

      <!-- Bandeau d'erreur : filet latéral d'état Carbon -->
      <div
        v-if="error"
        role="alert"
        class="mb-5 p-3 bg-cds-layer-01 border-l-2 border-cds-support-error flex items-center space-x-2"
      >
        <Lineicons
          :icon="Icons.error"
          :size="16"
          color="currentColor"
          class="shrink-0 text-cds-support-error"
        />
        <span class="text-xs text-cds-support-error">{{ error }}</span>
      </div>

      <!-- Formulaire -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="cds--form-item">
          <label class="cds--label" for="auth-email">Email professionnel</label>
          <input
            id="auth-email"
            v-model="form.email"
            type="email"
            required
            placeholder="contact@entreprise.com"
            class="cds--text-input placeholder:text-cds-text-placeholder"
          />
        </div>

        <div class="cds--form-item">
          <label class="cds--label" for="auth-password">Mot de passe</label>
          <input
            id="auth-password"
            v-model="form.password"
            type="password"
            required
            placeholder="Min. 8 caractères, 1 chiffre"
            class="cds--text-input placeholder:text-cds-text-placeholder"
          />
        </div>

        <template v-if="mode === 'register'">
          <div>
            <div class="cds--label">Votre rôle principal</div>
            <div class="grid grid-cols-2 gap-3">
              <label
                class="flex flex-col items-center justify-center p-3 border cursor-pointer transition text-center"
                :class="form.role === 'producer'
                  ? 'bg-cds-background-selected border-cds-border-interactive text-cds-text-primary'
                  : 'bg-cds-background border-cds-border-subtle text-cds-text-helper hover:border-cds-border-strong'"
              >
                <input type="radio" value="producer" v-model="form.role" class="sr-only" />
                <span class="text-sm font-bold">Producteur</span>
                <span class="text-[10px] text-cds-text-helper mt-0.5">Je génère des déchets</span>
              </label>

              <label
                class="flex flex-col items-center justify-center p-3 border cursor-pointer transition text-center"
                :class="form.role === 'collector'
                  ? 'bg-cds-background-selected border-cds-border-interactive text-cds-text-primary'
                  : 'bg-cds-background border-cds-border-subtle text-cds-text-helper hover:border-cds-border-strong'"
              >
                <input type="radio" value="collector" v-model="form.role" class="sr-only" />
                <span class="text-sm font-bold">Collecteur</span>
                <span class="text-[10px] text-cds-text-helper mt-0.5">Je collecte & valorise</span>
              </label>
            </div>
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="auth-organization">Nom de l'organisation / Entreprise</label>
            <input
              id="auth-organization"
              v-model="form.organization_name"
              type="text"
              placeholder="Ex: Plastique Recyclage SA"
              class="cds--text-input placeholder:text-cds-text-placeholder"
            />
          </div>

          <div class="cds--form-item">
            <label class="cds--label" for="auth-phone">Numéro de téléphone (avec indicatif)</label>
            <input
              id="auth-phone"
              v-model="form.phone"
              type="tel"
              required
              placeholder="+221 77 123 45 67"
              class="cds--text-input placeholder:text-cds-text-placeholder"
            />
          </div>
        </template>

        <button
          type="submit"
          :disabled="loading"
          class="cds--btn cds--btn--primary cds--btn--full mt-6"
        >
          <span class="flex items-center space-x-2">
            <Lineicons
              v-if="loading"
              :icon="Icons.loading"
              :size="16"
              color="currentColor"
              class="animate-spin"
            />
            <span>{{ mode === 'login' ? 'Se connecter' : "S'inscrire" }}</span>
          </span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'

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
const route = useRoute()

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

    // Retour à la page protégée demandée, sinon atterrissage selon le rôle
    const redirect = route.query.redirect
    if (typeof redirect === 'string' && redirect.startsWith('/')) {
      await navigateTo(redirect)
    } else {
      await navigateTo(res.user?.role === 'admin' ? '/admin' : '/marketplace')
    }
  } catch (err: any) {
    error.value = err.response?._data?.detail || err.message || 'Une erreur est survenue'
  } finally {
    loading.value = false
  }
}
</script>
