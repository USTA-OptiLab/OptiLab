<script setup>
import { computed } from 'vue'

const props = defineProps({
  estilo: { type: String, default: 'info' }, // 'ok' | 'aviso' | 'info'
  texto: { type: String, required: true },
})

const CLASES = {
  ok: 'bg-emerald-950/60 text-emerald-300 border-emerald-800',
  aviso: 'bg-amber-950/60 text-amber-300 border-amber-800',
  info: 'bg-neutral-900 text-neutral-300 border-neutral-800',
}

const clase = computed(() => CLASES[props.estilo] ?? CLASES.info)
</script>

<template>
  <p class="mb-2 rounded border px-3 py-2 text-sm font-medium" :class="clase">{{ texto }}</p>
</template>
