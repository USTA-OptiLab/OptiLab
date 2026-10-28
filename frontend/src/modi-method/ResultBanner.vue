<script setup>
import { computed } from 'vue'

const props = defineProps({
  estilo: { type: String, default: 'info' }, // 'ok' | 'aviso' | 'info'
  texto: { type: String, required: true },
})

const CLASES = {
  ok: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100',
  aviso: 'border-amber-500/30 bg-amber-500/10 text-amber-100',
  info: 'border-neutral-700 bg-neutral-900/50 text-neutral-300',
}

const clase = computed(() => CLASES[props.estilo] ?? CLASES.info)
</script>

<template>
  <p class="rounded-xl border px-3 py-2.5 text-sm font-medium" :class="clase">{{ texto }}</p>
</template>
