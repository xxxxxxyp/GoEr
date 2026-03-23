<script setup lang="ts">
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Database,
  Loader2,
  Plus,
  Radio,
  SearchCode,
  Trash2,
} from 'lucide-vue-next'
import { onMounted, ref } from 'vue'

import http from '../utils/http'

interface SubscriptionResponse {
  id: number
  user_id: number
  source_platform: string | null
  search_query: string | null
  cron_schedule: string | null
  is_active: boolean
}

interface CreateSubscriptionPayload {
  source_platform: string | null
  search_query: string | null
  cron_schedule: string | null
}

type FeedbackTone = 'success' | 'error' | null

const subscriptions = ref<SubscriptionResponse[]>([])
const isLoading = ref(true)
const isRefreshing = ref(false)
const isSubmitting = ref(false)
const deletingIds = ref<number[]>([])
const feedback = ref('')
const feedbackTone = ref<FeedbackTone>(null)

const sourcePlatform = ref('arxiv')
const searchQuery = ref('')
const cronSchedule = ref('0 8 * * *')

const cronOptions = [
  { label: '每天 8 点 (0 8 * * *)', value: '0 8 * * *' },
  { label: '每 12 小时 (0 */12 * * *)', value: '0 */12 * * *' },
]

const scheduleLabel = (cron: string | null): string => {
  if (!cron) return 'No schedule'

  const option = cronOptions.find((item) => item.value === cron)
  return option ? option.label : cron
}

const resetForm = () => {
  sourcePlatform.value = 'arxiv'
  searchQuery.value = ''
  cronSchedule.value = '0 8 * * *'
}

const setFeedback = (message: string, tone: FeedbackTone) => {
  feedback.value = message
  feedbackTone.value = tone
}

const fetchSubscriptions = async (silent = false) => {
  if (silent) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }

  try {
    const { data } = await http.get<SubscriptionResponse[]>('/subscriptions/')
    subscriptions.value = data
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
    setFeedback('Failed to sync subscriptions. Please retry.', 'error')
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

const submitRule = async () => {
  if (!searchQuery.value.trim()) {
    setFeedback('Search query is required to deploy a collector.', 'error')
    return
  }

  isSubmitting.value = true

  const payload: CreateSubscriptionPayload = {
    source_platform: sourcePlatform.value.trim() || null,
    search_query: searchQuery.value.trim(),
    cron_schedule: cronSchedule.value || null,
  }

  try {
    await http.post<SubscriptionResponse>('/subscriptions/', payload)
    resetForm()
    setFeedback('Collector deployed. Rule pool updated.', 'success')
    await fetchSubscriptions(true)
  } catch (error) {
    console.error('Failed to create subscription:', error)
    setFeedback('Deploy failed. Please check inputs and try again.', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const deleteRule = async (id: number) => {
  if (deletingIds.value.includes(id)) {
    return
  }

  const confirmed = window.confirm('Delete this subscription rule? This action cannot be undone.')
  if (!confirmed) {
    return
  }

  deletingIds.value.push(id)

  try {
    await http.delete(`/subscriptions/${id}`)
    subscriptions.value = subscriptions.value.filter((item) => item.id !== id)
    setFeedback('Subscription rule deleted.', 'success')
  } catch (error) {
    console.error(`Failed to delete subscription ${id}:`, error)
    setFeedback('Delete failed. Please try again.', 'error')
  } finally {
    deletingIds.value = deletingIds.value.filter((itemId) => itemId !== id)
  }
}

onMounted(() => {
  void fetchSubscriptions()
})
</script>

<template>
  <section class="space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.22em] text-slate-500">Signal Collector</p>
        <h3 class="mt-1 text-3xl font-semibold text-slate-900">Subscription Center</h3>
      </div>
      <div class="flex items-center gap-3">
        <span class="mono-chip !px-4 !py-2">{{ subscriptions.length }} active rules</span>
        <Loader2 v-if="isRefreshing" class="h-4 w-4 animate-spin text-sky-600" />
      </div>
    </header>

    <div class="grid gap-4 xl:grid-cols-[minmax(340px,420px),1fr]">
      <article class="glass-card p-5 sm:p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Area A</p>
            <h4 class="text-xl font-semibold text-slate-900">Deploy Rule</h4>
          </div>
          <Plus class="h-5 w-5 text-sky-600" />
        </div>

        <form class="space-y-4" @submit.prevent="submitRule">
          <label class="block">
            <span class="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Source Platform</span>
            <input
              v-model="sourcePlatform"
              type="text"
              placeholder="arxiv"
              class="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-sky-300"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Search Query</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="ti:ASVspoof AND abs:augmentation"
              class="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-sky-300"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cron Schedule</span>
            <select
              v-model="cronSchedule"
              class="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-sky-300"
            >
              <option
                v-for="option in cronOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>

          <button
            type="submit"
            :disabled="isSubmitting"
            class="inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-sky-300 bg-sky-500 px-4 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-70"
          >
            <Loader2 v-if="isSubmitting" class="h-4 w-4 animate-spin" />
            <span>{{ isSubmitting ? 'Deploying...' : 'Deploy Collector' }}</span>
          </button>
        </form>

        <p
          v-if="feedback"
          class="mt-4 flex items-center gap-2 rounded-xl border px-3 py-2 text-sm"
          :class="feedbackTone === 'success'
            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
            : 'border-rose-200 bg-rose-50 text-rose-700'"
        >
          <CheckCircle2 v-if="feedbackTone === 'success'" class="h-4 w-4" />
          <AlertCircle v-else class="h-4 w-4" />
          {{ feedback }}
        </p>
      </article>

      <article class="glass-card p-5 sm:p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Area B</p>
            <h4 class="text-xl font-semibold text-slate-900">Rule Pool</h4>
          </div>
          <Database class="h-5 w-5 text-slate-600" />
        </div>

        <div
          v-if="isLoading"
          class="grid min-h-[240px] place-content-center gap-3 text-center"
        >
          <Loader2 class="mx-auto h-7 w-7 animate-spin text-sky-600" />
          <p class="text-sm text-slate-600">Syncing subscriptions...</p>
        </div>

        <div
          v-else-if="subscriptions.length === 0"
          class="grid min-h-[240px] place-content-center gap-3 text-center"
        >
          <Radio class="mx-auto h-8 w-8 text-slate-500" />
          <p class="text-sm text-slate-600">
            No collectors deployed yet. Create your first rule on the left panel.
          </p>
        </div>

        <TransitionGroup
          v-else
          tag="div"
          class="space-y-3"
          enter-active-class="transition-all duration-200 ease-out"
          leave-active-class="transition-all duration-200 ease-in"
          leave-to-class="-translate-y-1 opacity-0"
        >
          <div
            v-for="subscription in subscriptions"
            :key="subscription.id"
            class="rounded-2xl border border-slate-200 bg-white/90 p-4"
          >
            <div class="mb-3 flex items-start justify-between gap-3">
              <div class="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                <component
                  :is="(subscription.source_platform || '').toLowerCase() === 'arxiv' ? Radio : Database"
                  class="h-4 w-4 text-sky-600"
                />
                <span>{{ subscription.source_platform || 'custom' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="mono-chip"
                  :class="subscription.is_active
                    ? '!border-emerald-200 !bg-emerald-50 !text-emerald-700'
                    : '!border-slate-200 !bg-slate-100 !text-slate-500'"
                >
                  {{ subscription.is_active ? 'Active' : 'Paused' }}
                </span>
                <button
                  type="button"
                  :disabled="deletingIds.includes(subscription.id)"
                  class="text-slate-400 hover:text-rose-500 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                  @click="deleteRule(subscription.id)"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>

            <div class="space-y-2 text-sm text-slate-600">
              <p class="inline-flex items-start gap-2">
                <SearchCode class="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <span>{{ subscription.search_query || 'No query' }}</span>
              </p>
              <p class="inline-flex items-start gap-2">
                <Clock3 class="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <span>{{ scheduleLabel(subscription.cron_schedule) }}</span>
              </p>
            </div>
          </div>
        </TransitionGroup>
      </article>
    </div>
  </section>
</template>
