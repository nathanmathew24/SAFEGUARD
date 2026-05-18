import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

// In production (Railway), VITE_API_URL is set to the backend service URL.
// In local dev, it's empty and the Vite proxy handles /api and /auth.
const BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${BASE}/api`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export const authApi = axios.create({
  baseURL: `${BASE}/auth`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})
