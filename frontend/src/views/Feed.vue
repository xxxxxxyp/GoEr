<script setup lang="ts">
import {
  ArrowUpRight,
  Check,
  CheckCheck,
  Inbox,
  Loader2,
  RefreshCw,
  Sparkles,
  Users,
} from 'lucide-vue-next'
import { onMounted, onUnmounted, ref } from 'vue'

import http from '../utils/http'

interface UnreadPaperResponse {
  interaction_id: number
  paper_title: string
  authors: string[]
  core_innovation: string | null
  relevance_score: number | null
  added_at: string
}

interface MessageResponse {
  message: string
}

const papers = ref<UnreadPaperResponse[]>([])
const isLoading = ref(true)
const readingIds = ref<number[]>([])
const isSyncing = ref(false)
const syncFeedback = ref('')
let syncFeedbackTimer: ReturnType<typeof setTimeout> | null = null

const fetchUnreadPapers = async () => {
  isLoading.value = true

  try {
    const { data } = await http.get<UnreadPaperResponse[]>('/papers/unread')
    papers.value = data
  } catch (error) {
    papers.value = []
    console.error('Failed to load unread papers:', error)
  } finally {
    isLoading.value = false
  }
}

const markAsRead = async (interactionId: number) => {
  if (readingIds.value.includes(interactionId)) {
    return
  }

  readingIds.value.push(interactionId)

  try {
    await http.post(`/papers/${interactionId}/read`)
    papers.value = papers.value.filter((paper) => paper.interaction_id !== interactionId)
  } catch (error) {
    console.error(`Failed to mark paper ${interactionId} as read:`, error)
  } finally {
    readingIds.value = readingIds.value.filter((id) => id !== interactionId)
  }
}

const openScholar = (title: string) => {
  const scholarUrl = `https://scholar.google.com/scholar?q=${encodeURIComponent(title)}`
  window.open(scholarUrl, '_blank', 'noopener,noreferrer')
}

const triggerSync = async () => {
  isSyncing.value = true

  try {
    const { data } = await http.post<MessageResponse>('/papers/trigger-fetch')
    syncFeedback.value = data.message

    if (syncFeedbackTimer) {
      clearTimeout(syncFeedbackTimer)
    }

    syncFeedbackTimer = setTimeout(() => {
      syncFeedback.value = ''
      syncFeedbackTimer = null
    }, 3000)
  } catch (error) {
    console.error('Failed to trigger sync:', error)
    syncFeedback.value = 'Failed to trigger sync. Please retry.'

    if (syncFeedbackTimer) {
      clearTimeout(syncFeedbackTimer)
    }

    syncFeedbackTimer = setTimeout(() => {
      syncFeedback.value = ''
      syncFeedbackTimer = null
    }, 3000)
  } finally {
    isSyncing.value = false
  }
}

const scoreTone = (score: number | null) => {
  if (score === null) return 'bg-slate-100 text-slate-500 border-slate-200'
  if (score >= 90) return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (score >= 80) return 'bg-sky-50 text-sky-700 border-sky-200'
  return 'bg-amber-50 text-amber-700 border-amber-200'
}

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))

onMounted(() => {
  void fetchUnreadPapers()
})

onUnmounted(() => {
  if (syncFeedbackTimer) {
    clearTimeout(syncFeedbackTimer)
  }
})
</script>

<template>
  <section class="space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.22em] text-slate-500">Unread Intelligence</p>
        <h3 class="mt-1 text-3xl font-semibold text-slate-900">Paper Feed</h3>
      </div>
      <div class="flex items-center gap-3">
        <div class="mono-chip !px-4 !py-2">{{ papers.length }} fresh signals</div>
        <button
          type="button"
          :disabled="isSyncing"
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-300 hover:text-sky-700 disabled:opacity-60"
          @click="triggerSync"
        >
          <RefreshCw class="h-4 w-4" :class="isSyncing ? 'animate-spin' : ''" />
          {{ isSyncing ? 'Syncing...' : 'Sync Now' }}
        </button>
      </div>
    </header>

    <p
      v-if="syncFeedback"
      class="-mt-2 inline-flex items-center gap-2 text-sm text-emerald-600"
    >
      <Check class="h-4 w-4" />
      {{ syncFeedback }}
    </p>

    <div
      v-if="isLoading"
      class="glass-card grid min-h-[300px] place-content-center gap-3 text-center"
    >
      <Loader2 class="mx-auto h-8 w-8 animate-spin text-sky-600" />
      <p class="text-sm font-medium text-slate-600">Syncing intelligence...</p>
    </div>

    <div
      v-else-if="papers.length === 0"
      class="glass-card grid min-h-[300px] place-content-center gap-3 text-center"
    >
      <Inbox class="mx-auto h-9 w-9 text-slate-500" />
      <p class="text-base font-medium text-slate-700">
        Inbox Zero. You are fully caught up with the latest research.
      </p>
      <p class="text-sm text-slate-500">New summaries will appear here after the next sync cycle.</p>
    </div>

    <TransitionGroup
      v-else
      tag="div"
      class="space-y-4"
      enter-active-class="transition-all duration-200 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      leave-to-class="-translate-y-1 scale-[0.99] opacity-0"
    >
      <article
        v-for="paper in papers"
        :key="paper.interaction_id"
        class="glass-card relative overflow-hidden p-5 sm:p-6"
      >
        <div class="pointer-events-none absolute right-0 top-0 h-24 w-24 rounded-bl-[48px] bg-gradient-to-br from-sky-200/60 to-emerald-200/50" />

        <div class="relative">
          <div class="mb-4 flex flex-wrap items-center gap-2">
            <span class="mono-chip">#{{ paper.interaction_id }}</span>
            <span class="rounded-full border px-2.5 py-1 text-xs" :class="scoreTone(paper.relevance_score)">
              AI score: {{ paper.relevance_score ?? 'N/A' }}
            </span>
            <span class="text-xs text-slate-500">Added {{ formatDate(paper.added_at) }}</span>
          </div>

          <h4 class="max-w-3xl text-xl font-semibold text-slate-900">
            {{ paper.paper_title }}
          </h4>

          <div class="mt-3 flex items-start gap-2 text-sm text-slate-600">
            <Users class="mt-0.5 h-4 w-4 text-slate-500" />
            <p>{{ paper.authors.join(', ') }}</p>
          </div>

          <div class="mt-5 rounded-2xl border border-sky-200 bg-sky-50/70 p-4">
            <div class="mb-2 flex items-center gap-2">
              <Sparkles class="h-4 w-4 text-sky-600" />
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">Core Innovation</p>
            </div>
            <p class="text-sm leading-relaxed text-slate-700">
              {{
                paper.core_innovation ||
                'Innovation summary is still being generated by Qwen. Retry in a few minutes.'
              }}
            </p>
          </div>

          <div class="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              :disabled="readingIds.includes(paper.interaction_id)"
              class="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
              @click="markAsRead(paper.interaction_id)"
            >
              <CheckCheck class="h-4 w-4" />
              {{ readingIds.includes(paper.interaction_id) ? 'Marking...' : 'Mark as read' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-xl border border-sky-200 bg-white px-4 py-2 text-sm font-medium text-sky-700 transition hover:bg-sky-50"
              @click="openScholar(paper.paper_title)"
            >
              <ArrowUpRight class="h-4 w-4" />
              View PDF
            </button>
          </div>
        </div>
      </article>
    </TransitionGroup>
  </section>
</template>
