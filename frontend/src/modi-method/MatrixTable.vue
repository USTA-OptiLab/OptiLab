<script setup>
import { computed } from 'vue'
import { num } from '../format.js'

const props = defineProps({
  problema: { type: Object, required: true },
  iteracion: { type: Object, required: true },
  potenciales: { type: Boolean, default: false },
  deltas: { type: Boolean, default: false },
  ciclo: { type: Boolean, default: false },
  decimales: { type: Number, default: 2 },
})

const EPS = 1e-9

const basicas = computed(() => new Set(props.iteracion.basicas.map(([i, j]) => `${i},${j}`)))
const signos = computed(() => {
  const m = new Map()
  if (props.ciclo) for (const [i, j, s] of props.iteracion.ciclo) m.set(`${i},${j}`, s)
  return m
})
const totalOferta = computed(() => props.problema.oferta.reduce((a, b) => a + b, 0))

function es(par, i, j) {
  return !!par && par[0] === i && par[1] === j
}
const entra = (i, j) => props.ciclo && es(props.iteracion.entrante, i, j)
const sale = (i, j) => props.ciclo && es(props.iteracion.sale, i, j)

function claseCelda(i, j) {
  const k = `${i},${j}`
  if (entra(i, j)) return 'bg-emerald-500/25 outline outline-2 -outline-offset-2 outline-emerald-400'
  if (sale(i, j)) return 'bg-amber-500/20 outline outline-2 -outline-offset-2 outline-amber-400'
  const s = signos.value.get(k)
  if (s > 0) return 'bg-emerald-500/10 outline outline-2 -outline-offset-2 outline-emerald-600/70'
  if (s < 0) return 'bg-rose-500/10 outline outline-2 -outline-offset-2 outline-rose-600/70'
  if (basicas.value.has(k)) return 'bg-indigo-500/15'
  return 'bg-neutral-900/60'
}

const esFicticio = (nombre) => nombre === 'Ficticio'
</script>

<template>
  <div class="overflow-x-auto rounded-lg border border-neutral-800">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr class="bg-neutral-800/70 text-neutral-300">
          <th class="px-3 py-2 text-left text-xs font-medium text-neutral-500">Origen ＼ Destino</th>
          <th v-for="(d, j) in problema.destinos" :key="`h-${j}`" class="px-3 py-2 font-semibold" :class="{ 'italic text-neutral-400': esFicticio(d) }">{{ d }}</th>
          <th class="px-3 py-2 font-semibold text-amber-300">Oferta</th>
          <th v-if="potenciales" class="px-3 py-2 font-semibold text-sky-300">u<sub>i</sub></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(o, i) in problema.origenes" :key="`r-${i}`">
          <th class="whitespace-nowrap bg-neutral-800/40 px-3 py-2 text-left font-semibold text-neutral-200" :class="{ 'italic text-neutral-400': esFicticio(o) }">{{ o }}</th>
          <td
            v-for="(_d, j) in problema.destinos" :key="`c-${i}-${j}`"
            class="relative h-[4.5rem] min-w-[6rem] border border-neutral-800 text-center align-middle"
            :class="claseCelda(i, j)"
          >
            <span class="absolute left-1.5 top-1 text-xs text-neutral-500">c={{ num(problema.costos[i][j], decimales) }}</span>
            <span
              v-if="signos.has(`${i},${j}`)"
              class="absolute right-1 top-1 rounded-full px-1.5 text-[13px] font-bold leading-4"
              :class="signos.get(`${i},${j}`) > 0 ? 'bg-emerald-400 text-emerald-950' : 'bg-rose-400 text-rose-950'"
            >{{ signos.get(`${i},${j}`) > 0 ? '+' : '−' }}</span>

            <span v-if="basicas.has(`${i},${j}`)" class="text-lg font-bold text-indigo-200">{{ num(iteracion.asignacion[i][j], decimales) }}</span>
            <span
              v-else-if="deltas && iteracion.delta[i][j] != null"
              class="text-sm font-semibold"
              :class="iteracion.delta[i][j] < -EPS ? 'text-rose-300' : 'text-neutral-400'"
            >Δ = {{ num(iteracion.delta[i][j], decimales) }}</span>

            <span v-if="entra(i, j)" class="absolute inset-x-0 bottom-1 text-xs font-semibold uppercase tracking-wide text-emerald-300">entra</span>
            <span v-else-if="sale(i, j)" class="absolute inset-x-0 bottom-1 text-xs font-semibold uppercase tracking-wide text-amber-300">sale</span>
          </td>
          <td class="bg-amber-500/5 px-3 py-2 text-center font-semibold text-amber-200">{{ num(problema.oferta[i], decimales) }}</td>
          <td v-if="potenciales" class="bg-sky-500/10 px-3 py-2 text-center font-semibold text-sky-200">{{ num(iteracion.u[i], decimales) }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr class="bg-amber-500/5 font-semibold text-amber-200">
          <th class="px-3 py-2 text-left">Demanda</th>
          <td v-for="(dem, j) in problema.demanda" :key="`dm-${j}`" class="px-3 py-2 text-center">{{ num(dem, decimales) }}</td>
          <td class="px-3 py-2 text-center text-neutral-400">Σ {{ num(totalOferta, decimales) }}</td>
          <td v-if="potenciales"></td>
        </tr>
        <tr v-if="potenciales" class="bg-sky-500/10 font-semibold text-sky-200">
          <th class="px-3 py-2 text-left">v<sub>j</sub></th>
          <td v-for="(vj, j) in iteracion.v" :key="`v-${j}`" class="px-3 py-2 text-center">{{ num(vj, decimales) }}</td>
          <td></td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>
