<script setup lang="ts">
import { Lock, UserRound } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const submitLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = 'Username and password are required.'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(username.value, password.value)
    await router.push('/')
  } catch {
    errorMessage.value = 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="relative grid min-h-screen place-items-center overflow-hidden px-4 py-8">
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_8%,rgba(14,165,233,0.18),transparent_28%),radial-gradient(circle_at_88%_20%,rgba(34,197,94,0.16),transparent_30%)]" />

    <div class="glass-card relative w-full max-w-md p-7 sm:p-8">
      <p class="mono-chip inline-flex">goer://auth</p>
      <h1 class="mt-3 text-3xl font-semibold text-slate-900">Login</h1>
      <p class="mt-2 text-sm text-slate-600">Enter your credentials to access your personal academic intel station.</p>

      <form class="mt-7 space-y-4" @submit.prevent="submitLogin">
        <label class="block">
          <span class="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Username</span>
          <div class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
            <UserRound class="h-4 w-4 text-slate-500" />
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              class="h-11 w-full border-0 bg-transparent text-slate-900 outline-none placeholder:text-slate-400"
              placeholder="your_username"
            />
          </div>
        </label>

        <label class="block">
          <span class="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Password</span>
          <div class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
            <Lock class="h-4 w-4 text-slate-500" />
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="h-11 w-full border-0 bg-transparent text-slate-900 outline-none placeholder:text-slate-400"
              placeholder="••••••••"
            />
          </div>
        </label>

        <p v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ errorMessage }}
        </p>

        <button
          type="submit"
          :disabled="loading"
          class="inline-flex h-11 w-full items-center justify-center rounded-xl border border-sky-300 bg-sky-500 px-4 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {{ loading ? 'Signing in...' : 'Login' }}
        </button>
      </form>
    </div>
  </section>
</template>
