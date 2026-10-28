<script setup>
import { ref } from 'vue'

const count = ref(0)
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 bg-neutral-950 text-neutral-100">
    <h1 class="text-3xl font-semibold">OptiLab</h1>
    <p class="text-neutral-400">Vue + Tailwind, served by pywebview</p>
    <button
      class="rounded-md bg-indigo-600 px-4 py-2 font-medium hover:bg-indigo-500"
      @click="count++"
    >
      count is {{ count }}
    </button>
  </div>
</template>
