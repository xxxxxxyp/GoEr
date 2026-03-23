import axios, { AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from 'axios'

import router from '../router'

const http = axios.create({
  baseURL: '/api/v1',
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')

  if (token) {
    const headers =
      config.headers instanceof AxiosHeaders
        ? config.headers
        : new AxiosHeaders(config.headers)

    headers.set('Authorization', `Bearer ${token}`)
    config.headers = headers
  }

  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')

      if (router.currentRoute.value.path !== '/login') {
        await router.push('/login')
      }
    }

    return Promise.reject(error)
  },
)

export default http
