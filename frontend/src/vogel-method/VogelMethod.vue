<script setup>
import { computed, ref } from 'vue'
import VogelResults from './VogelResults.vue'

const MIN_SIZE = 1
const MAX_SIZE = 8
const exampleCases = [
  {
    id: 'balanced',
    name: 'Balanceado',
    maximize: false,
    costs: [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
    supply: [7, 9, 18],
    demand: [5, 8, 7, 14],
  },
  {
    id: 'unbalanced',
    name: 'Desbalanceado',
    maximize: false,
    costs: [[4, 6, 8], [5, 3, 7]],
    supply: [30, 40],
    demand: [20, 15, 10],
  },
  {
    id: 'maximize',
    name: 'Maximización',
    maximize: true,
    costs: [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
    supply: [7, 9, 18],
    demand: [5, 8, 7, 14],
  },
]

const rowCount = ref(3)
const colCount = ref(4)
const costs = ref([])
const supply = ref([])
const demand = ref([])
const context = ref('')
const maximize = ref(false)
const result = ref(null)
const error = ref('')
const loading = ref(false)

function loadExample(example) {
  rowCount.value = example.supply.length
  colCount.value = example.demand.length
  costs.value = example.costs.map((row) => [...row])
  supply.value = [...example.supply]
  demand.value = [...example.demand]
  context.value = example.id === 'balanced'
    ? 'Una empresa tiene 3 fábricas y debe distribuir productos a 4 almacenes, buscando minimizar los costos de transporte.'
    : example.id === 'unbalanced'
      ? 'Una empresa distribuye productos desde 2 orígenes hacia 3 destinos y dispone de más oferta que demanda.'
      : 'Una empresa distribuye productos desde 3 orígenes hacia 4 destinos, buscando maximizar las ganancias.'
  maximize.value = example.maximize
  resetResult()
}

function resetResult() {
  result.value = null
  error.value = ''
}

loadExample(exampleCases[0])

function resizeProblem(nextRows, nextCols) {
  const rows = Math.max(MIN_SIZE, Math.min(MAX_SIZE, nextRows))
  const cols = Math.max(MIN_SIZE, Math.min(MAX_SIZE, nextCols))
  if (rows === rowCount.value && cols === colCount.value) return
  costs.value = Array.from({ length: rows }, (_, i) =>
    Array.from({ length: cols }, (_, j) => costs.value[i]?.[j] ?? 0),
  )
  supply.value = Array.from({ length: rows }, (_, i) => supply.value[i] ?? 0)
  demand.value = Array.from({ length: cols }, (_, j) => demand.value[j] ?? 0)
  rowCount.value = rows
  colCount.value = cols
  resetResult()
}

const isValidNumber = (value) => value !== '' && value !== null &&
  value !== undefined && Number.isFinite(Number(value)) && Number(value) >= 0

const isValid = computed(() =>
  supply.value.every(isValidNumber) &&
  demand.value.every(isValidNumber) &&
  costs.value.every((row) => row.every(isValidNumber)),
)
const supplyTotal = computed(() => supply.value.reduce((acc, item) => acc + (Number(item) || 0), 0))
const demandTotal = computed(() => demand.value.reduce((acc, item) => acc + (Number(item) || 0), 0))
const difference = computed(() => supplyTotal.value - demandTotal.value)
const balanced = computed(() => Math.abs(difference.value) <= 1e-9 * Math.max(1, supplyTotal.value, demandTotal.value))
const formatNumber = (value) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 3 }).format(value)

async function calculate() {
  resetResult()
  if (!isValid.value) {
    error.value = 'Revisa la matriz: todos los costos, ofertas y demandas deben ser números no negativos.'
    return
  }
  if (!window.pywebview?.api?.solve_vogel) {
    error.value = 'La conexión con Python no está disponible. Abre OptiLab con «just dev» o «just run» para calcular.'
    return
  }
  loading.value = true
  try {
    const problem = {
      costs: costs.value.map((row) => row.map(Number)),
      supply: supply.value.map(Number),
      demand: demand.value.map(Number),
      maximize: maximize.value,
      context: context.value,
    }
    // Send only plain JSON over pywebview; structuredClone() breaks WebKitGTK.
    const response = await window.pywebview.api.solve_vogel(JSON.parse(JSON.stringify(problem)))
    if (response?.status !== 'success' || !response.result) {
      throw new Error(response?.message || 'No se pudo resolver el problema.')
    }
    result.value = response.result
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  } finally {
    loading.value = false
  }
}

function resetAll() {
  loadExample(exampleCases[0])
}
</script>

<template>
  <section>
    <div class="mb-8 flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
      <div>
        <div class="mb-3 flex items-center gap-2 text-xs font-semibold text-indigo-300">
          <span class="rounded-md border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 uppercase tracking-[0.16em]">VAM</span>
          <span class="text-slate-500">/</span>
          <span class="text-slate-400">Problema de transporte</span>
        </div>
        <h1 class="text-3xl font-bold tracking-tight text-white sm:text-[38px]">Método de Vogel<span class="text-indigo-400">.</span></h1>
        <p class="mt-3 max-w-2xl text-sm leading-relaxed text-slate-400">
          Construye tu matriz, define la oferta y la demanda, y analiza la solución inicial paso a paso.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-400">
        <span class="rounded-full border border-white/10 bg-white/5 px-3 py-2">01 · Datos</span>
        <span class="text-slate-600">→</span>
        <span class="rounded-full border border-white/10 bg-white/5 px-3 py-2">02 · Cálculo</span>
        <span class="text-slate-600">→</span>
        <span class="rounded-full border border-white/10 bg-white/5 px-3 py-2">03 · Resultados</span>
      </div>
    </div>

    <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_290px]">
      <div class="min-w-0 rounded-2xl border border-white/10 bg-[#101624] shadow-2xl shadow-black/10">
        <div class="flex flex-col justify-between gap-4 border-b border-white/8 px-5 py-5 sm:flex-row sm:items-center sm:px-6">
          <div>
            <h2 class="text-base font-semibold text-white">Configuración del problema</h2>
            <p class="mt-1 text-xs text-slate-500">Edita valores y dimensiones directamente en la matriz</p>
          </div>
          <button class="self-start rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/5" @click="resetAll">
            ↺ Restablecer
          </button>
        </div>

        <div class="space-y-7 p-5 sm:p-6">
          <div>
            <label for="problem-context" class="mb-3 block text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Contexto del problema <span class="font-normal normal-case tracking-normal text-slate-500">(opcional)</span></label>
            <textarea id="problem-context" v-model="context" rows="3" placeholder="Describe la empresa, qué se transporta y cuál es el objetivo del problema…" class="w-full resize-y rounded-xl border border-white/10 bg-[#0a0f1a] px-4 py-3 text-sm leading-relaxed text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-indigo-400" @input="resetResult"></textarea>
          </div>

          <div>
            <p class="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Objetivo de optimización</p>
            <div class="flex max-w-sm gap-1 rounded-xl border border-white/10 bg-[#0a0f1a] p-1">
              <button
                class="flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold transition"
                :class="!maximize ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-950/30' : 'text-slate-400 hover:text-white'"
                :aria-pressed="!maximize"
                @click="maximize = false; resetResult()"
              >Minimizar costos</button>
              <button
                class="flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold transition"
                :class="maximize ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-950/30' : 'text-slate-400 hover:text-white'"
                :aria-pressed="maximize"
                @click="maximize = true; resetResult()"
              >Maximizar ganancias</button>
            </div>
          </div>

          <div class="flex flex-wrap items-end gap-8">
            <div>
              <p class="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Orígenes</p>
              <div class="flex items-center rounded-xl border border-white/10 bg-[#0a0f1a]">
                <button class="h-10 w-11 text-xl text-slate-300 transition hover:text-white disabled:opacity-25" aria-label="Quitar un origen" :disabled="rowCount <= MIN_SIZE" @click="resizeProblem(rowCount - 1, colCount)">−</button>
                <span class="min-w-10 text-center text-sm font-semibold tabular-nums">{{ rowCount }}</span>
                <button class="h-10 w-11 text-xl text-slate-300 transition hover:text-white disabled:opacity-25" aria-label="Añadir un origen" :disabled="rowCount >= MAX_SIZE" @click="resizeProblem(rowCount + 1, colCount)">+</button>
              </div>
            </div>
            <div>
              <p class="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Destinos</p>
              <div class="flex items-center rounded-xl border border-white/10 bg-[#0a0f1a]">
                <button class="h-10 w-11 text-xl text-slate-300 transition hover:text-white disabled:opacity-25" aria-label="Quitar un destino" :disabled="colCount <= MIN_SIZE" @click="resizeProblem(rowCount, colCount - 1)">−</button>
                <span class="min-w-10 text-center text-sm font-semibold tabular-nums">{{ colCount }}</span>
                <button class="h-10 w-11 text-xl text-slate-300 transition hover:text-white disabled:opacity-25" aria-label="Añadir un destino" :disabled="colCount >= MAX_SIZE" @click="resizeProblem(rowCount, colCount + 1)">+</button>
              </div>
            </div>
          </div>

          <div>
            <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Matriz de {{ maximize ? 'ganancias' : 'costos' }}</p>
              <span class="text-xs text-slate-500">Valores ≥ 0 · Hasta 8 × 8</span>
            </div>
            <div class="overflow-x-auto rounded-xl border border-white/10">
              <table class="w-full min-w-max border-separate border-spacing-0 text-center text-sm">
                <thead>
                  <tr class="bg-[#1b2537] text-xs font-semibold text-slate-300">
                    <th class="sticky left-0 z-10 min-w-23 border-b border-r border-white/10 bg-[#1b2537] px-3 py-3 text-left">Origen</th>
                    <th v-for="j in colCount" :key="'head-'+j" class="min-w-22 border-b border-r border-white/10 px-2 py-3">D{{ j }}</th>
                    <th class="min-w-24 border-b border-white/10 bg-indigo-500/8 px-3 py-3 text-indigo-300">Oferta</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="i in rowCount" :key="'row-'+i" class="bg-[#111a2a]">
                    <th class="sticky left-0 z-10 border-b border-r border-white/8 bg-[#1b2537] px-3 py-2 text-left text-xs font-semibold text-slate-300">O{{ i }}</th>
                    <td v-for="j in colCount" :key="'cell-'+i+'-'+j" class="border-b border-r border-white/8 p-1.5">
                      <input v-model.number="costs[i-1][j-1]" type="number" min="0" step="any" :aria-label="`${maximize ? 'Ganancia' : 'Costo'} O${i} D${j}`" class="w-18 rounded-md border border-transparent bg-[#0a101d] px-2 py-2.5 text-center text-sm tabular-nums text-white outline-none transition hover:border-white/15 focus:border-indigo-400 focus:bg-[#0c1426]" @input="resetResult" />
                    </td>
                    <td class="border-b border-white/8 bg-indigo-500/5 p-1.5">
                      <input v-model.number="supply[i-1]" type="number" min="0" step="any" :aria-label="`Oferta de origen ${i}`" class="w-19 rounded-md border border-indigo-400/15 bg-[#0a101d] px-2 py-2.5 text-center text-sm font-semibold tabular-nums text-indigo-200 outline-none transition focus:border-indigo-400" @input="resetResult" />
                    </td>
                  </tr>
                  <tr class="bg-[#1b2537]">
                    <th class="sticky left-0 z-10 border-r border-white/10 bg-[#1b2537] px-3 py-3 text-left text-xs font-semibold text-emerald-300">Demanda</th>
                    <td v-for="j in colCount" :key="'demand-'+j" class="border-r border-white/10 bg-emerald-500/5 p-1.5">
                      <input v-model.number="demand[j-1]" type="number" min="0" step="any" :aria-label="`Demanda de destino ${j}`" class="w-18 rounded-md border border-emerald-400/15 bg-[#0a101d] px-2 py-2.5 text-center text-sm font-semibold tabular-nums text-emerald-200 outline-none transition focus:border-emerald-400" @input="resetResult" />
                    </td>
                    <td class="px-3 py-3 text-xs font-semibold text-slate-400">Total</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="mt-3 text-xs text-slate-500">O = origen · D = destino · La celda representa el {{ maximize ? 'beneficio' : 'costo' }} unitario.</p>
          </div>

          <div v-if="error" role="alert" class="rounded-xl border border-rose-400/25 bg-rose-500/10 px-4 py-3 text-sm leading-relaxed text-rose-200">{{ error }}</div>

          <div class="flex flex-col items-start justify-between gap-4 border-t border-white/10 pt-5 sm:flex-row sm:items-center">
            <span class="text-xs text-slate-500">Se calculará una solución inicial factible con VAM.</span>
            <button :disabled="loading" class="inline-flex w-full items-center justify-center gap-3 rounded-xl bg-indigo-500 px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:cursor-wait disabled:opacity-60 sm:w-auto" @click="calculate">
              {{ loading ? 'Calculando…' : 'Resolver problema' }} <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-5">
        <div class="rounded-2xl border border-white/10 bg-[#101624] p-5 sm:p-6">
          <p class="mb-5 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Resumen del problema</p>
          <div class="space-y-4">
            <div class="flex items-center justify-between gap-4"><span class="text-sm text-slate-400">Oferta total</span><span class="text-xl font-bold tabular-nums text-white">{{ formatNumber(supplyTotal) }}</span></div>
            <div class="h-px bg-white/8"></div>
            <div class="flex items-center justify-between gap-4"><span class="text-sm text-slate-400">Demanda total</span><span class="text-xl font-bold tabular-nums text-white">{{ formatNumber(demandTotal) }}</span></div>
            <div class="h-px bg-white/8"></div>
            <div class="flex items-center justify-between gap-3"><span class="text-sm text-slate-400">Estado</span><span class="rounded-full px-3 py-1.5 text-xs font-semibold" :class="balanced ? 'bg-emerald-400/10 text-emerald-300' : 'bg-amber-400/10 text-amber-300'">{{ balanced ? '● Balanceado' : '● Desbalanceado' }}</span></div>
          </div>
          <div v-if="!balanced" class="mt-5 rounded-xl border border-amber-400/15 bg-amber-400/5 p-4 text-xs leading-relaxed text-amber-200/90">
            {{ difference > 0 ? `Sobran ${formatNumber(difference)} unidades de oferta.` : `Faltan ${formatNumber(Math.abs(difference))} unidades de oferta.` }} El algoritmo agregará {{ difference > 0 ? 'un destino' : 'un origen' }} ficticio automáticamente.
          </div>
        </div>

        <div class="rounded-2xl border border-white/10 bg-[#101624] p-5 sm:p-6">
          <p class="mb-4 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Cargar ejemplo</p>
          <div class="space-y-2">
            <button v-for="example in exampleCases" :key="example.id" class="flex w-full items-center justify-between rounded-lg border border-white/8 bg-white/[0.025] px-4 py-3 text-left text-sm font-medium text-slate-300 transition hover:border-indigo-400/30 hover:bg-indigo-500/10 hover:text-white" @click="loadExample(example)">
              {{ example.name }} <span class="text-slate-500">↗</span>
            </button>
          </div>
        </div>

        <div class="rounded-2xl border border-indigo-400/15 bg-indigo-400/[0.055] p-5 sm:p-6">
          <div class="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-400/15 text-indigo-200">ⓘ</div>
          <h3 class="text-sm font-semibold text-white">¿Qué calcula Vogel?</h3>
          <p class="mt-2 text-xs leading-6 text-slate-400">Compara las dos mejores celdas de cada fila y columna, elige la mayor penalización y asigna unidades hasta cubrir la demanda y agotar la oferta.</p>
          <p class="mt-3 text-xs leading-relaxed text-indigo-300/80">Es una solución inicial; no garantiza el óptimo global.</p>
        </div>
      </div>
    </div>

    <VogelResults v-if="result" :result="result" class="mt-7" />
  </section>
</template>
