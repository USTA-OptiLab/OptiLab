<script setup>
import VogelMethod from './vogel-method/VogelMethod.vue'
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-[#080c15] font-sans text-slate-100 antialiased">
    <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div class="absolute -top-56 left-1/3 h-96 w-96 rounded-full bg-indigo-700/10 blur-[110px]"></div>
      <div class="absolute top-1/2 -right-52 h-96 w-96 rounded-full bg-cyan-500/5 blur-[110px]"></div>
    </div>

    <main class="relative mx-auto w-full max-w-[1440px] px-4 pb-14 pt-8 sm:px-7 lg:px-10 lg:pt-12">
      <VogelMethod />
    </main>
  </div>
</template>
