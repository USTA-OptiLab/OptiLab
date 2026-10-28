<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  bloques: { type: Array, default: () => [] },
  pasoAPaso: { type: Boolean, default: false },
})

const paso = ref(0)

watch(
  () => props.bloques,
  () => { paso.value = 0 },
)

const visibles = computed(() => (props.pasoAPaso ? props.bloques.slice(0, paso.value + 1) : props.bloques))
const texto = computed(() => visibles.value.join('\n\n'))

function lineaClase(linea, enTitulo) {
  if (linea.startsWith('==========')) return 'text-neutral-500'
  if (enTitulo) return 'bg-indigo-950 font-bold text-indigo-300'
  if (linea.includes('<- negativo')) return 'text-rose-400'
  if (linea.startsWith('Entra la celda')) return 'font-bold text-emerald-400'
  if (linea.startsWith('Todos los Δ') || linea.startsWith('Costo total =') || linea.startsWith('Ganancia total =')) return 'font-bold text-emerald-400'
  return ''
}

const lineas = computed(() => {
  const resultado = []
  let enTitulo = false
  for (const linea of texto.value.split('\n')) {
    const esSeparador = linea.startsWith('==========')
    resultado.push({ texto: linea, clase: lineaClase(linea, enTitulo) })
    if (esSeparador) enTitulo = !enTitulo
  }
  return resultado
})

function ir(delta) {
  paso.value = Math.max(0, Math.min(props.bloques.length - 1, paso.value + delta))
}

defineExpose({ resolver: () => (paso.value = 0) })
</script>

<template>
  <div class="flex h-full flex-col">
    <pre class="flex-1 overflow-auto rounded border border-neutral-800 bg-neutral-950 p-3 font-mono text-xs leading-5"><span
        v-for="(l, k) in lineas" :key="k" :class="l.clase"
      >{{ l.texto }}<br /></span></pre>
    <div v-if="pasoAPaso" class="mt-2 flex items-center gap-2 text-sm">
      <button type="button" class="rounded border border-neutral-700 px-2 py-1 disabled:opacity-30" :disabled="paso === 0" @click="ir(-1)">◀ Anterior</button>
      <button type="button" class="rounded border border-neutral-700 px-2 py-1 disabled:opacity-30" :disabled="paso >= bloques.length - 1" @click="ir(1)">Siguiente ▶</button>
      <span class="text-neutral-400">Paso {{ paso + 1 }} de {{ bloques.length }}</span>
    </div>
  </div>
</template>
