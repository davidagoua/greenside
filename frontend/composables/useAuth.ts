import type { User } from '~/types'

export const useAuth = () => {
  const token = useCookie<string | null>('ecoloop_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 days
    sameSite: 'lax'
  })
  const user = useState<User | null>('auth_user', () => null)
  const config = useRuntimeConfig()

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const role = computed(() => user.value?.role || null)

  const fetchCurrentUser = async () => {
    if (!token.value) {
      user.value = null
      return null
    }
    try {
      const data = await $fetch<User>(`${config.public.apiBaseUrl}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })
      user.value = data
      return data
    } catch (err) {
      token.value = null
      user.value = null
      return null
    }
  }

  const setAuth = (newToken: string, newUser: User) => {
    token.value = newToken
    user.value = newUser
  }

  const logout = () => {
    token.value = null
    user.value = null
    navigateTo('/auth')
  }

  return {
    token,
    user,
    isAuthenticated,
    role,
    fetchCurrentUser,
    setAuth,
    logout
  }
}
