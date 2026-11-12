<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import GranMMethod from './gran-m-method/GranMMethod.vue'
import TwoPhaseSolver from './two-phase/TwoPhaseSolver.vue'
import GraphicMethod from './graphic-method/GraphicMethod.vue'
import PrimalDualView from './primal-dual/PrimalDualView.vue'
import ModiMethod from './modi-method/ModiMethod.vue'
import SimplexMethod from './simplex-method/SimplexMethod.vue'
import VogelMethod from './vogel-method/VogelMethod.vue'

// Cada método nuevo se agrega aquí para que aparezca en el menú
const methods = [
  {
    id: 'simplex',
    short: 'Tablas, pivotes e informe final',
    family: 'lineal',
    name: 'Método Simplex',
    description: 'Programación lineal primal con tablas paso a paso, pivotes, análisis de sensibilidad y contexto de negocio.',
    component: SimplexMethod,
  },
  {
    id: 'gran-m',
    short: 'Penaliza las artificiales con M',
    family: 'lineal',
    name: 'Método de la Gran M',
    description: 'Programación lineal con penalización M para las variables artificiales.',
    component: GranMMethod,
  },
  {
    id: 'two-phase',
    short: 'Factibilidad y luego óptimo',
    family: 'lineal',
    name: 'Método de las Dos Fases',
    description: 'Programación lineal con variables artificiales: factibilidad y luego optimalidad.',
    component: TwoPhaseSolver,
  },
  {
    id: 'graphic',
    short: 'Región factible y vértices',
    family: 'lineal',
    name: 'Método Gráfico',
    description: 'Programación lineal con dos variables: región factible, vértices y solución óptima.',
    component: GraphicMethod,
  },
  {
    id: 'primal-dual',
    short: 'Construye y resuelve el dual',
    family: 'lineal',
    name: 'Primal → Dual',
    description: 'Construye el dual de un problema de programación lineal y lo resuelve con Simplex exacto.',
    component: PrimalDualView,
  },
  {
    id: 'modi',
    short: 'Mejora la solución inicial',
    family: 'transporte',
    name: 'Método MODI',
    description: 'Problema de transporte: solución inicial, iteraciones MODI, análisis de sensibilidad y comparación de métodos.',
    component: ModiMethod,
  },
  {
    id: 'vogel',
    short: 'Aproximación con penalizaciones',
    family: 'transporte',
    name: 'Método de Vogel',
    description: 'Problema de transporte: aproximación de Vogel con penalizaciones, contexto de negocio e interpretación de resultados.',
    component: VogelMethod,
  },
]

// Orden visto en clase (el arreglo de arriba solo registra los métodos)
const ORDER = ['graphic', 'simplex', 'gran-m', 'two-phase', 'primal-dual', 'vogel', 'modi']
const ordered = ORDER.map((id) => methods.find((m) => m.id === id))
const families = [
  { id: 'lineal', title: 'Programación lineal', cols: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5' },
  { id: 'transporte', title: 'Transporte', cols: 'grid-cols-2' },
].map((f) => ({ ...f, items: ordered.filter((m) => m.family === f.id) }))
const number = (m) => ORDER.indexOf(m.id) + 1

const current = shallowRef(null)
const open = (m) => {
  current.value = m
  paletteOpen.value = false
  window.scrollTo(0, 0)
}
const home = () => {
  current.value = null
  window.scrollTo(0, 0)
}

// --- Cuadro rotativo de la portada: ejemplos ilustrativos de cada método ---
const slides = [
  { id: 'graphic', title: 'Gráfico', sub: 'Región factible', kind: 'graph', foot: 'La región factible y el vértice óptimo: (2, 6) con Z = 36.' },
  { id: 'simplex', title: 'Simplex', sub: 'Tabla 0', head: ['Base', 'x₁', 'x₂', 's₁', 's₂', 's₃', 'B'], rows: [['Z', '-3', '-5', '0', '0', '0', '0'], ['s₁', '1', '0', '1', '0', '0', '4'], ['s₂', '0', '2', '0', '1', '0', '12'], ['s₃', '3', '2', '0', '0', '1', '18']], pivot: [2, 2], foot: 'Entra x₂, sale s₂: 12 ÷ 2 = 6 es la menor razón.' },
  { id: 'gran-m', title: 'Gran M', sub: 'Tabla inicial', head: ['Base', 'x₁', 'x₂', 'S₁', 'S₃', 'A₁', 'A₂', 'B'], rows: [['Z', '-2/5', '-1/2', '0', '0', '-M', '-M', '0'], ['S₁', '3/10', '1/10', '1', '0', '0', '0', '27/10'], ['A₁', '1/2', '1/2', '0', '0', '1', '0', '6'], ['A₂', '3/5', '2/5', '0', '-1', '0', '1', '6']], foot: 'Las artificiales A₁ y A₂ se penalizan con M en la fila Z.' },
  { id: 'two-phase', title: 'Dos Fases', sub: 'Fase 1 · Iteración 1', head: ['Variable', 'Coeficiente', 'Razón'], rows: [['A₁', '2', '12 ÷ 2 = 6'], ['A₂', '1', '8 ÷ 1 = 8'], ['S₃', '0', 'no participa']], pivot: [0, 2], foot: 'Primero factibilidad, luego optimalidad: al final de la Fase 2, Z = 74.' },
  { id: 'primal-dual', title: 'Primal → Dual', sub: 'Dualidad fuerte', kind: 'dual', foot: 'Z primal = Z dual = 22: se verifica la dualidad fuerte.' },
  { id: 'vogel', title: 'Vogel', sub: 'Paso 1 · Penalizaciones', head: ['', 'D1', 'D2', 'D3', 'D4', 'Penal.'], rows: [['O1', '19', '30', '50', '10', '9'], ['O2', '70', '30', '40', '60', '10'], ['O3', '40', '8', '70', '20', '12'], ['Penal.', '21', '22', '10', '10', '']], pivot: [3, 2], foot: 'Mayor penalización: 22 en D2. Se asigna en su celda de menor costo.' },
  { id: 'modi', title: 'MODI', sub: 'Costos reducidos Δ', head: ['Δ', 'D1', 'D2', 'D3', 'D4'], rows: [['O1', '·', '32', '60', '·'], ['O2', '1', '-18', '·', '·'], ['O3', '11', '·', '70', '·']], pivot: [1, 2], foot: 'Δ negativo: la solución mejora. El costo baja de 779 a 743.' },
].map((s) => ({ ...s, method: methods.find((m) => m.id === s.id) }))

const SLIDE_MS = 5000
const slide = ref(0)
const tick = ref(0) // reinicia la barra de progreso
const paused = ref(false)
const reduceMotion = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches
let timer = null
const stop = () => clearInterval(timer)
const start = () => {
  stop()
  if (!reduceMotion) timer = setInterval(() => goSlide(slide.value + 1, false), SLIDE_MS)
}
const goSlide = (i, restart = true) => {
  slide.value = (i + slides.length) % slides.length
  tick.value++
  if (restart) start()
}
const hoverIn = () => { paused.value = true; stop() }
const hoverOut = () => { paused.value = false; tick.value++; start() }

// --- Buscador de métodos (Ctrl K) ---
const paletteOpen = ref(false)
const query = ref('')
const selected = ref(0)
const searchInput = ref(null)
const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  return ordered.filter((m) => !q || `${m.name} ${m.description}`.toLowerCase().includes(q))
})
const openPalette = async () => {
  paletteOpen.value = true
  query.value = ''
  selected.value = 0
  await nextTick()
  searchInput.value?.focus()
}
const onKey = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    openPalette()
    return
  }
  if (paletteOpen.value) {
    if (e.key === 'Escape') paletteOpen.value = false
    else if (e.key === 'ArrowDown') { e.preventDefault(); selected.value = Math.min(selected.value + 1, results.value.length - 1) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); selected.value = Math.max(selected.value - 1, 0) }
    else if (e.key === 'Enter' && results.value[selected.value]) open(results.value[selected.value])
    return
  }
  if (e.key === 'Escape' && current.value && !e.target.closest?.('input, textarea, select')) home()
}
onMounted(() => { window.addEventListener('keydown', onKey); start() })
onBeforeUnmount(() => { window.removeEventListener('keydown', onKey); stop() })

const pill = 'rounded-full border border-neutral-700 bg-neutral-900 font-medium transition hover:border-neutral-100'
</script>

<template>
  <div class="min-h-screen bg-neutral-950 text-neutral-100">
    <header class="sticky top-0 z-30 flex items-center gap-3 border-b border-neutral-800 bg-neutral-950/95 px-7 py-2.5">
      <button class="group flex items-center gap-2 px-1 py-1.5 text-lg font-semibold tracking-tight" aria-label="OptiLab, ir al inicio" @click="home">
        <i class="block size-2.5 rotate-45 rounded-xs bg-indigo-300 transition-transform duration-500 ease-out group-hover:rotate-225" />
        OptiLab
      </button>
      <button v-if="current" :class="[pill, 'flex items-center gap-2 px-3.5 py-1.5 text-sm active:scale-95']" @click="home">
        <svg viewBox="0 0 24 24" class="size-4 fill-none stroke-current" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5" /><path d="M5.5 10v9.5h13V10" /></svg>
        Inicio
      </button>
      <span v-if="current" class="text-sm text-neutral-400">/ <b class="font-medium text-neutral-100">{{ current.name }}</b></span>
      <span class="flex-1" />
      <button :class="[pill, 'flex min-w-64 items-center justify-between gap-6 px-4 py-1.5 text-sm text-neutral-400 hover:text-neutral-100']" @click="openPalette">
        Buscar método
        <kbd class="rounded-md border border-neutral-700 px-1.5 py-0.5 font-mono text-xs">Ctrl K</kbd>
      </button>
    </header>

    <component :is="current.component" v-if="current" />

    <main v-else class="mx-auto w-full max-w-[1220px] px-7 pt-8 pb-12">
      <section class="grid items-center gap-12 lg:grid-cols-[1fr_1.12fr]">
        <div>
          <h1 class="text-5xl leading-none font-semibold tracking-tighter text-balance sm:text-6xl">
            Resuelve, <span class="text-indigo-300">y entiende por qué.</span>
          </h1>
          <p class="mt-5 max-w-[38ch] text-lg text-neutral-400">
            Siete métodos de programación lineal y transporte, con cada tabla, cada decisión y la interpretación del resultado.
          </p>
        </div>

        <div class="flex min-h-[300px] flex-col rounded-2xl border border-neutral-700 bg-neutral-900 px-5 pt-4 pb-3.5" @mouseenter="hoverIn" @mouseleave="hoverOut">
          <div :key="slide" class="flex flex-1 flex-col">
            <div class="mb-2.5 flex items-baseline justify-between">
              <b class="text-base font-semibold tracking-tight">{{ slides[slide].title }}</b>
              <span class="text-sm text-neutral-400">{{ slides[slide].sub }}</span>
            </div>
            <div class="flex min-h-[220px] flex-1 flex-col justify-center">
              <div v-if="slides[slide].kind === 'graph'" aria-hidden="true">
                <svg viewBox="0 0 380 300" class="max-h-60 w-full">
                  <g class="stroke-neutral-600" stroke-width="1"><line x1="36" y1="268" x2="360" y2="268" /><line x1="36" y1="268" x2="36" y2="12" /></g>
                  <polygon points="36,268 196,268 196,172 116,76 36,76" class="fill-indigo-300/15 stroke-indigo-300" stroke-width="1.5" />
                  <line x1="36" y1="44" x2="276" y2="140" class="stroke-neutral-400" stroke-dasharray="5 4" />
                  <circle cx="116" cy="76" r="6" class="fill-indigo-300" />
                  <text x="128" y="68" class="fill-neutral-100 text-[13px]">Óptimo (2, 6)</text>
                </svg>
              </div>
              <div v-else-if="slides[slide].kind === 'dual'" class="grid grid-cols-2 gap-3">
                <div class="rounded-lg border border-neutral-800 p-3"><h4 class="mb-1 text-xs text-neutral-400">Primal</h4><p class="font-mono text-sm leading-relaxed">máx 4x₁ + 3x₂<br>2x₁ + x₂ ≤ 10<br>x₁ + 2x₂ ≤ 8</p></div>
                <div class="rounded-lg border border-neutral-800 p-3"><h4 class="mb-1 text-xs text-neutral-400">Dual</h4><p class="font-mono text-sm leading-relaxed">mín 10y₁ + 8y₂<br>2y₁ + y₂ ≥ 4<br>y₁ + 2y₂ ≥ 3</p></div>
              </div>
              <div v-else class="overflow-x-auto">
                <table class="w-full border-collapse text-center font-mono text-sm tabular-nums">
                  <thead><tr><th v-for="h in slides[slide].head" :key="h" scope="col" class="border-b border-neutral-700 px-2 py-1.5 font-medium text-neutral-400">{{ h }}</th></tr></thead>
                  <tbody>
                    <tr v-for="(row, r) in slides[slide].rows" :key="r" class="border-b border-neutral-800">
                      <td v-for="(c, i) in row" :key="i" class="px-2 py-1.5" :class="[i === 0 ? 'text-left font-semibold' : '', slides[slide].pivot && slides[slide].pivot[0] === r && slides[slide].pivot[1] === i ? 'rounded bg-indigo-300 font-semibold text-neutral-950' : '', r === 0 && String(c).startsWith('-') ? 'text-red-300' : '']">{{ c }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="mt-2.5 flex items-center justify-between gap-3 text-sm">
              <p class="max-w-[46ch]">{{ slides[slide].foot }}</p>
              <button :class="[pill, 'shrink-0 px-3 py-1 text-xs active:scale-95']" @click="open(slides[slide].method)">Abrir método →</button>
            </div>
          </div>
          <div class="mt-3 flex gap-1.5 border-t border-neutral-800 pt-3">
            <button v-for="(s, j) in slides" :key="s.id" class="relative flex h-6.5 flex-1 items-end pb-1.5 text-left text-xs" :class="j === slide ? 'text-neutral-100' : 'text-neutral-400'" :aria-label="s.title" :aria-current="j === slide" @click="goSlide(j)">
              <span class="absolute inset-x-0 top-0 h-[3px] rounded-full bg-neutral-700" />
              <span v-if="j === slide" :key="tick" class="absolute top-0 left-0 h-[3px] rounded-full bg-indigo-300" :class="reduceMotion ? 'w-full' : 'animate-[llena_5s_linear_forwards]'" :style="{ animationPlayState: paused ? 'paused' : 'running' }" />
              {{ s.title.split(' ')[0] }}
            </button>
          </div>
        </div>
      </section>

      <section class="mt-9 grid gap-7 lg:grid-cols-[5fr_2fr]">
        <div v-for="f in families" :key="f.id">
          <h2 class="mb-2.5 flex justify-between border-b border-neutral-700 pb-2 text-sm font-semibold text-neutral-400">
            {{ f.title }} <span>{{ f.items.length }}</span>
          </h2>
          <div class="grid gap-2" :class="f.cols">
            <button v-for="m in f.items" :key="m.id" class="group relative flex min-h-33 flex-col gap-1 rounded-xl border border-neutral-800 bg-neutral-900 p-3 pb-10 text-left transition duration-300 ease-out hover:-translate-y-0.5 hover:border-indigo-300 hover:bg-neutral-900 active:scale-[.99]" @click="open(m)">
              <span class="font-mono text-xs text-neutral-400">{{ number(m) }}</span>
              <b class="text-lg leading-tight font-semibold tracking-tight">{{ m.name.replace('Método de las ', '').replace('Método de la ', '').replace('Método de ', '').replace('Método ', '') }}</b>
              <span class="text-sm leading-snug text-neutral-400">{{ m.short }}</span>
              <i class="absolute right-3 bottom-3 grid size-6 place-items-center rounded-full border border-neutral-700 text-neutral-100 transition group-hover:border-indigo-300 group-hover:bg-indigo-300 group-hover:text-neutral-950">→</i>
            </button>
          </div>
        </div>
      </section>
    </main>

    <div v-if="paletteOpen" class="fixed inset-0 z-50 grid content-start justify-items-center bg-black/60 pt-[14vh]" @click.self="paletteOpen = false">
      <div role="dialog" aria-label="Buscar método" class="w-[min(560px,92vw)] overflow-hidden rounded-2xl border border-neutral-700 bg-neutral-900 shadow-2xl">
        <input ref="searchInput" v-model="query" placeholder="Buscar un método…" autocomplete="off" class="w-full border-0 border-b border-neutral-800 bg-transparent px-4.5 py-4 text-base outline-none" @input="selected = 0" />
        <ul class="max-h-[50vh] overflow-auto p-1.5">
          <li v-for="(m, i) in results" :key="m.id">
            <button class="flex w-full justify-between rounded-lg px-3 py-2.5 text-left" :class="i === selected ? 'bg-indigo-300 text-neutral-950' : ''" @click="open(m)">
              {{ m.name }}
              <small :class="i === selected ? 'text-neutral-950' : 'text-neutral-400'">{{ m.family === 'lineal' ? 'Programación lineal' : 'Transporte' }}</small>
            </button>
          </li>
          <li v-if="!results.length" class="p-3.5 text-neutral-400">Ningún método coincide.</li>
        </ul>
      </div>
    </div>
  </div>
</template>
