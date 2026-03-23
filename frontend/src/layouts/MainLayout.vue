<script setup lang="ts">
import { Bell, Compass, Database, Home, Rss, Search } from 'lucide-vue-next'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  {
    label: 'Dashboard',
    to: '/',
    icon: Home,
  },
  {
    label: 'Feed',
    to: '/feed',
    icon: Rss,
  },
  {
    label: 'Sources',
    to: '/subscriptions',
    icon: Database,
  },
]

const isActive = (to: string) => {
  if (to === '/') {
    return route.path === '/'
  }

  return route.path.startsWith(to)
}
</script>

<template>
  <div class="min-h-screen bg-goer-bg bg-mesh p-3 md:p-6">
    <div class="mx-auto flex min-h-[calc(100vh-1.5rem)] w-full max-w-[1320px] flex-col overflow-hidden rounded-3xl border border-white/70 bg-white/75 shadow-halo backdrop-blur md:min-h-[calc(100vh-3rem)] md:flex-row">
      <aside class="w-full border-b border-slate-200/70 bg-slate-950 px-6 py-6 text-slate-100 md:w-72 md:border-b-0 md:border-r md:border-r-slate-800/90">
        <div class="mb-8 flex items-center gap-3">
          <div class="grid h-11 w-11 place-content-center rounded-xl bg-gradient-to-br from-sky-400 to-emerald-400 text-slate-950">
            <Compass class="h-5 w-5" />
          </div>
          <div>
            <p class="mono-chip !border-slate-700 !bg-slate-900 !text-sky-300">goer://intel</p>
            <h1 class="text-lg font-semibold leading-none text-white">GoEr Station</h1>
          </div>
        </div>

        <nav class="space-y-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center justify-between rounded-xl border px-4 py-3 transition"
            :class="isActive(item.to)
              ? 'border-sky-300/30 bg-sky-400/10 text-sky-200'
              : 'border-slate-800 bg-slate-900/70 text-slate-300 hover:border-slate-600 hover:text-white'"
          >
            <div class="flex items-center gap-3">
              <component :is="item.icon" class="h-4 w-4" />
              <span class="text-sm font-medium">{{ item.label }}</span>
            </div>
            <span class="mono-chip !border-slate-700 !bg-slate-800/70 !text-slate-200">{{ item.label.slice(0, 2).toUpperCase() }}</span>
          </RouterLink>
        </nav>

        <div class="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <p class="text-xs uppercase tracking-[0.22em] text-slate-400">Signal State</p>
          <p class="mt-2 text-sm font-medium text-slate-100">Collectors healthy, feed syncing every 10m.</p>
        </div>
      </aside>

      <section class="flex-1 overflow-hidden bg-white/70">
        <header class="flex h-20 items-center justify-between border-b border-slate-200 px-5 md:px-8">
          <div>
            <p class="text-xs uppercase tracking-[0.24em] text-slate-400">Personal Research Ops</p>
            <h2 class="text-xl font-semibold text-slate-900">Academic Intel Dashboard</h2>
          </div>

          <div class="flex items-center gap-3">
            <button class="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-sky-300 hover:text-sky-700 md:inline-flex">
              <Search class="h-4 w-4" />
              Search
            </button>
            <button class="grid h-10 w-10 place-content-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:border-sky-300 hover:text-sky-700">
              <Bell class="h-4 w-4" />
            </button>
          </div>
        </header>

        <main class="h-[calc(100vh-8.5rem)] overflow-y-auto px-5 py-6 md:h-[calc(100vh-10.5rem)] md:px-8">
          <RouterView />
        </main>
      </section>
    </div>
  </div>
</template>
