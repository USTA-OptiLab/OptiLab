<script setup>
import { computed } from 'vue'
import IteracionCard from './IteracionCard.vue'
import Interpretacion from './Interpretacion.vue'
import MatrixTable from './MatrixTable.vue'
import ResultadoFinal from './ResultadoFinal.vue'
import { NOMBRES_METODO, num } from '../format.js'

const props = defineProps({
  resultado: { type: Object, required: true },
  opciones: { type: Object, required: true },
})

const detallado = computed(() => props.opciones.paso_a_paso)
const dec = computed(() => props.opciones.decimales)
const inicial = computed(() => props.resultado.historial[0])
const etiqueta = computed(() => (props.opciones.modo === 'maximizar' ? 'Ganancia' : 'Costo'))

const indice = computed(() => {
  const lista = []
  if (detallado.value && props.opciones.mostrar_inicial) lista.push({ id: 'paso-inicial', texto: 'Solución inicial' })
  if (detallado.value) {
    props.resultado.historial.forEach((it, k) => lista.push({ id: `paso-${k}`, texto: it.entrante === null && k > 0 ? `Iteración ${it.numero} (óptima)` : `Iteración ${it.numero}` }))
  }
  lista.push({ id: 'paso-final', texto: 'Resultado' }, { id: 'paso-interpretacion', texto: 'Interpretación' })
  return lista
})

function ir(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="space-y-5">
    <nav class="sticky top-0 z-10 -mx-1 flex flex-wrap gap-2 bg-neutral-950/90 px-1 py-2 backdrop-blur">
      <button
        v-for="(item, k) in indice" :key="item.id" type="button"
        class="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-indigo-500 hover:text-indigo-300"
        @click="ir(item.id)"
      >{{ k + 1 }}. {{ item.texto }}</button>
    </nav>

    <section v-if="detallado && opciones.mostrar_inicial" id="paso-inicial" class="scroll-mt-14 rounded-xl border border-neutral-800 bg-neutral-900/30">
      <header class="flex flex-wrap items-center gap-3 border-b border-neutral-800 px-4 py-3">
        <span class="flex h-8 w-8 items-center justify-center rounded-full bg-violet-500 text-sm font-bold text-white">0</span>
        <h3 class="text-lg font-semibold">Solución inicial — {{ NOMBRES_METODO[opciones.metodo_inicial] }}</h3>
        <span class="ml-auto rounded-full bg-neutral-800 px-3 py-1 text-sm text-neutral-300">
          {{ etiqueta }} inicial: <strong class="text-neutral-100">{{ num(resultado.costo_inicial, dec) }}</strong>
        </span>
      </header>
      <div class="space-y-3 p-4">
        <p class="text-sm text-neutral-400">
          Se construye una primera solución factible con m + n − 1 = {{ resultado.problema.m + resultado.problema.n - 1 }} celdas básicas
          (<span class="text-indigo-300">azul</span>); las demás valen cero. El método MODI parte de aquí para mejorarla.
        </p>
        <MatrixTable :problema="resultado.problema" :iteracion="inicial" :decimales="dec" />
      </div>
    </section>

    <template v-if="detallado">
      <div v-for="(it, k) in resultado.historial" :id="`paso-${k}`" :key="k" class="scroll-mt-14">
        <IteracionCard :resultado="resultado" :k="k" :opciones="opciones" />
      </div>
    </template>

    <div id="paso-final" class="scroll-mt-14"><ResultadoFinal :resultado="resultado" :opciones="opciones" /></div>
    <div id="paso-interpretacion" class="scroll-mt-14"><Interpretacion :resultado="resultado" :opciones="opciones" /></div>
  </div>
</template>
