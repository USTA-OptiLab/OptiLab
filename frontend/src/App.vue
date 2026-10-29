<script setup>
import PrimalDualView from './primal-dual/PrimalDualView.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <header class="border-b border-slate-800 px-6 py-4">
      <h1 class="text-xl font-semibold">OptiLab</h1>
    </header>
    <main class="mx-auto max-w-5xl p-6">
      <PrimalDualView />
    </main>
  </div>
</template>
