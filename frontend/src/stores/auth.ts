import { defineStore } from 'pinia'

import http from '../utils/http'

interface LoginResponse {
  access_token: string
  token_type?: string
}

interface AuthState {
  token: string | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => {
    const token = localStorage.getItem('token')

    return {
      token,
      isAuthenticated: Boolean(token),
    }
  },
  actions: {
    async login(username: string, password: string): Promise<void> {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const { data } = await http.post<LoginResponse>(
        '/auth/login/access-token',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        },
      )

      this.token = data.access_token
      this.isAuthenticated = true
      localStorage.setItem('token', data.access_token)
    },
    logout(): void {
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    },
  },
})
