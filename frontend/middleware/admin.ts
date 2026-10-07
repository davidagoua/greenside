/**
 * Garde d'accès au back-office : exige une session valide **et** le rôle `admin`.
 *
 * Exécutée côté client uniquement : en SSR, l'URL de l'API (`NUXT_PUBLIC_API_BASE_URL`,
 * soit `http://localhost:8000` en Docker) n'est pas joignable depuis le conteneur
 * frontend. Le HTML initial est donc un squelette sans données ; les pages admin
 * chargent leurs données dans `onMounted`, après validation de la garde.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const { token, user, fetchCurrentUser } = useAuth()
  const loginUrl = `/auth?redirect=${encodeURIComponent(to.fullPath)}`

  if (!token.value) {
    return navigateTo(loginUrl)
  }

  if (!user.value) {
    await fetchCurrentUser()
  }

  // fetchCurrentUser purge le cookie si le jeton est rejeté par l'API
  if (!token.value) {
    return navigateTo(loginUrl)
  }

  if (user.value?.role !== 'admin') {
    return navigateTo('/marketplace')
  }
})
