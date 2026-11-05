<script setup>
import { computed } from 'vue'
import MatrixTable from './MatrixTable.vue'
import { num } from '../format.js'

const props = defineProps({
  resultado: { type: Object, required: true },
  opciones: { type: Object, required: true },
})

const EPS = 1e-9
const p = computed(() => props.resultado.problema)
const final = computed(() => props.resultado.historial[props.resultado.historial.length - 1])
const dec = computed(() => props.opciones.decimales)
const etiqueta = computed(() => (props.opciones.modo === 'maximizar' ? 'Ganancia' : 'Costo'))

const rutas = computed(() => {
  const lista = []
  for (let i = 0; i < p.value.m; i++) {
    for (let j = 0; j < p.value.n; j++) {
      const q = final.value.asignacion[i][j]
      if (q <= EPS) continue
      const ficticia = i === props.resultado.fila_ficticia || j === props.resultado.columna_ficticia
      lista.push({ origen: p.value.origenes[i], destino: p.value.destinos[j], q, c: p.value.costos[i][j], ficticia })
    }
  }
  return lista
})

const estado = computed(() => {
  if (!props.resultado.optimo) return { clase: 'border-amber-700 bg-amber-950/50 text-amber-300', texto: `No convergió en ${props.opciones.max_iteraciones} iteraciones: el resultado puede no ser óptimo.` }
  const extra = props.resultado.optimos_alternativos ? ' Existen soluciones óptimas alternativas con el mismo valor.' : ''
  return { clase: 'border-emerald-700 bg-emerald-950/50 text-emerald-300', texto: `Solución óptima encontrada en ${props.resultado.mejoras} iteración(es) de mejora.${extra}` }
})
</script>

<template>
  <section class="rounded-xl border border-neutral-800 bg-neutral-900/30">
    <header class="flex items-center gap-3 border-b border-neutral-800 px-4 py-3">
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-emerald-950">✓</span>
      <h3 class="text-lg font-semibold">Resultado final</h3>
    </header>
    <div class="space-y-4 p-4">
      <div class="rounded-lg border px-4 py-3 font-medium" :class="estado.clase">{{ estado.texto }}</div>

      <MatrixTable :problema="p" :iteracion="final" :decimales="dec" />

      <div class="overflow-x-auto rounded-lg border border-neutral-800">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-neutral-800/70 text-left text-neutral-300">
              <th class="px-3 py-2">Ruta</th>
              <th class="px-3 py-2 text-right">Cantidad</th>
              <th class="px-3 py-2 text-right">Costo unitario</th>
              <th class="px-3 py-2 text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rutas" :key="`${r.origen}-${r.destino}`" class="border-t border-neutral-800" :class="r.ficticia ? 'italic text-neutral-500' : ''">
              <td class="px-3 py-2">{{ r.origen }} → {{ r.destino }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ num(r.q, dec) }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ num(r.c, dec) }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ num(r.q * r.c, dec) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t-2 border-neutral-700 bg-indigo-500/10 font-semibold">
              <td class="px-3 py-2" colspan="3">{{ etiqueta }} total</td>
              <td class="px-3 py-2 text-right font-mono text-lg text-indigo-200">{{ num(resultado.costo, dec) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </section>
</template>
