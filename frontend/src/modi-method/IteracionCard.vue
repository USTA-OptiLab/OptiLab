<script setup>
import { computed } from 'vue'
import MatrixTable from './MatrixTable.vue'
import { conParentesis, num } from '../format.js'

const props = defineProps({
  resultado: { type: Object, required: true },
  k: { type: Number, required: true },
  opciones: { type: Object, required: true },
})

const EPS = 1e-9
const it = computed(() => props.resultado.historial[props.k])
const siguiente = computed(() => props.resultado.historial[props.k + 1] ?? null)
const p = computed(() => props.resultado.problema)
const dec = computed(() => props.opciones.decimales)
// Al maximizar el programa resuelve con los costos negados; las ecuaciones deben mostrar esos.
const signo = computed(() => (props.opciones.modo === 'maximizar' ? -1 : 1))
const costoTrabajo = (i, j) => signo.value * p.value.costos[i][j]
const ruta = (i, j) => `${p.value.origenes[i]} → ${p.value.destinos[j]}`

const basicasSet = computed(() => new Set(it.value.basicas.map(([i, j]) => `${i},${j}`)))
const filasPotenciales = computed(() =>
  it.value.basicas.map(([i, j]) => ({
    ruta: ruta(i, j),
    eq: `u${i + 1} + v${j + 1} = ${num(costoTrabajo(i, j), dec.value)}`,
    calculo: `${conParentesis(it.value.u[i], dec.value)} + ${conParentesis(it.value.v[j], dec.value)} = ${num(costoTrabajo(i, j), dec.value)}`,
  })),
)
const filasDelta = computed(() => {
  const filas = []
  const entrante = it.value.entrante
  for (let i = 0; i < p.value.m; i++) {
    for (let j = 0; j < p.value.n; j++) {
      if (basicasSet.value.has(`${i},${j}`)) continue
      const d = it.value.delta[i][j]
      filas.push({
        ruta: ruta(i, j),
        calculo: `${num(costoTrabajo(i, j), dec.value)} − ${conParentesis(it.value.u[i], dec.value)} − ${conParentesis(it.value.v[j], dec.value)}`,
        delta: d,
        entra: !!entrante && entrante[0] === i && entrante[1] === j,
      })
    }
  }
  return filas
})
const negativas = computed(() => it.value.ciclo.filter(([, , s]) => s < 0))
const costoNuevo = computed(() => siguiente.value?.costo ?? props.resultado.costo)
const etiquetaCosto = computed(() => (props.opciones.modo === 'maximizar' ? 'Ganancia' : 'Costo'))
const titulo = computed(() => props.resultado.titulos[props.k])
const esUltima = computed(() => it.value.entrante === null)

const tarjeta = 'rounded-lg border border-neutral-800 bg-neutral-900/50 p-3'
</script>

<template>
  <section class="rounded-xl border border-neutral-800 bg-neutral-900/30">
    <header class="flex flex-wrap items-center gap-3 border-b border-neutral-800 px-4 py-3">
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">{{ it.numero }}</span>
      <h3 class="text-lg font-semibold">{{ titulo }}</h3>
      <span class="ml-auto rounded-full bg-neutral-800 px-3 py-1 text-sm text-neutral-300">
        {{ etiquetaCosto }} actual: <strong class="text-neutral-100">{{ num(it.costo, dec) }}</strong>
      </span>
    </header>

    <div class="space-y-4 p-4">
      <MatrixTable
        v-if="opciones.mostrar_asignacion_por_iteracion"
        :problema="p" :iteracion="it" :decimales="dec"
        :potenciales="opciones.mostrar_potenciales" :deltas="opciones.mostrar_costos_reducidos" :ciclo="opciones.mostrar_ciclo"
      />

      <div class="grid gap-4 lg:grid-cols-2">
        <div v-if="opciones.mostrar_potenciales" :class="tarjeta">
          <h4 class="mb-1 text-sm font-semibold text-sky-300">1. Potenciales u<sub>i</sub>, v<sub>j</sub></h4>
          <p class="mb-2 text-xs text-neutral-400">Para cada celda básica se cumple u<sub>i</sub> + v<sub>j</sub> = c<sub>ij</sub>, con u<sub>1</sub> = 0.</p>
          <table class="w-full text-sm">
            <thead><tr class="text-left text-xs text-neutral-500"><th class="py-1">Celda básica</th><th>Ecuación</th><th>Valores</th></tr></thead>
            <tbody>
              <tr v-for="f in filasPotenciales" :key="f.ruta" class="border-t border-neutral-800">
                <td class="py-1 pr-2">{{ f.ruta }}</td>
                <td class="pr-2 font-mono text-sky-200">{{ f.eq }}</td>
                <td class="font-mono text-neutral-300">{{ f.calculo }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="opciones.mostrar_costos_reducidos" :class="tarjeta">
          <h4 class="mb-1 text-sm font-semibold text-rose-300">2. Costos reducidos Δ<sub>ij</sub></h4>
          <p class="mb-2 text-xs text-neutral-400">Δ<sub>ij</sub> = c<sub>ij</sub> − u<sub>i</sub> − v<sub>j</sub> en celdas no básicas. Si alguno es negativo, la solución mejora.</p>
          <table class="w-full text-sm">
            <thead><tr class="text-left text-xs text-neutral-500"><th class="py-1">Celda</th><th>c − u − v</th><th class="text-right">Δ</th></tr></thead>
            <tbody>
              <tr
                v-for="f in filasDelta" :key="f.ruta"
                class="border-t border-neutral-800"
                :class="f.entra ? 'bg-emerald-500/15' : f.delta < -EPS ? 'bg-rose-500/10' : ''"
              >
                <td class="py-1 pr-2">{{ f.ruta }}<span v-if="f.entra" class="ml-2 rounded bg-emerald-400 px-1.5 text-[10px] font-bold uppercase text-emerald-950">entra</span></td>
                <td class="pr-2 font-mono text-neutral-300">{{ f.calculo }}</td>
                <td class="text-right font-mono font-semibold" :class="f.delta < -EPS ? 'text-rose-300' : 'text-neutral-300'">{{ num(f.delta, dec) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="esUltima" class="rounded-lg border border-emerald-700 bg-emerald-950/50 px-4 py-3 text-emerald-300">
        <strong>Todos los Δ ≥ 0:</strong> la solución actual es óptima. No hay ninguna celda que reduzca el costo al entrar a la base.
      </div>

      <div v-else-if="opciones.mostrar_ciclo" :class="tarjeta">
        <h4 class="mb-2 text-sm font-semibold text-amber-300">3. Ciclo de ajuste</h4>
        <p class="mb-3 text-sm text-neutral-300">
          Entra <strong class="text-emerald-300">{{ ruta(...it.entrante) }}</strong>
          (Δ = {{ num(it.delta[it.entrante[0]][it.entrante[1]], dec) }}, el más negativo según el criterio elegido). Se recorre el ciclo alternando + y −:
        </p>
        <div class="mb-3 flex flex-wrap gap-2">
          <span
            v-for="[i, j, s] in it.ciclo" :key="`${i}-${j}`"
            class="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm"
            :class="s > 0 ? 'border-emerald-600/60 bg-emerald-500/10 text-emerald-200' : 'border-rose-600/60 bg-rose-500/10 text-rose-200'"
          >
            <b class="text-base">{{ s > 0 ? '+' : '−' }}</b>{{ ruta(i, j) }}
            <span class="text-xs text-neutral-400">({{ num(it.asignacion[i][j], dec) }})</span>
          </span>
        </div>
        <ul class="space-y-1 text-sm text-neutral-300">
          <li>
            θ = mín { {{ negativas.map(([i, j]) => num(it.asignacion[i][j], dec)).join(', ') }} } =
            <strong class="text-amber-300">{{ num(it.theta, dec) }}</strong>
            <span class="text-neutral-500"> (lo mínimo de las celdas con signo −)</span>
          </li>
          <li>Sale de la base: <strong class="text-amber-300">{{ ruta(...it.sale) }}</strong></li>
          <li>
            {{ etiquetaCosto }}: <span class="font-mono">{{ num(it.costo, dec) }}</span> → <strong class="font-mono text-emerald-300">{{ num(costoNuevo, dec) }}</strong>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
