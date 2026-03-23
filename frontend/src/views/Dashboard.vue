<template>
  <section class="space-y-6">
    <div class="glass-card p-6">
      <h3 class="text-2xl font-semibold text-slate-900">Mission Control</h3>
      <p class="mt-2 max-w-2xl text-slate-600">
        This board will aggregate collector status, summarization latency, and source-level activity.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <article class="glass-card p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500">New Papers</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">42</p>
      </article>
      <article class="glass-card p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500">AI Summaries</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">38</p>
      </article>
      <article class="glass-card p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Active Sources</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">7</p>
      </article>
      <article class="glass-card p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Queue Delay</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">4m</p>
      </article>
    </div>
  </section>
</template>
