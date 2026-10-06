export const useApi = () => {
  const config = useRuntimeConfig()
  const { token, logout } = useAuth()

  const apiFetch = async <T>(endpoint: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> => {
    const headers: Record<string, string> = {
      ...((options.headers as Record<string, string>) || {})
    }

    if (token.value) {
      headers['Authorization'] = `Bearer ${token.value}`
    }

    try {
      return await $fetch<T>(`${config.public.apiBaseUrl}${endpoint}`, {
        ...options,
        headers
      })
    } catch (err: any) {
      if (err.response?.status === 401) {
        logout()
      }
      throw err
    }
  }

  return {
    apiFetch
  }
}
