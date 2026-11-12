<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import ComparisonTable from './ComparisonTable.vue'
import NetworkDiagram from './NetworkDiagram.vue'
import OptionsPanel from './OptionsPanel.vue'
import ProblemGrid from './ProblemGrid.vue'
import ProcedureOptions from './ProcedureOptions.vue'
import PasosView from './PasosView.vue'
import ResultBanner from './ResultBanner.vue'
import SensitivityTable from './SensitivityTable.vue'
import { num } from '../format.js'

const TAMANO_TEXTO_DEFECTO = 12
const TAMANO_TEXTO_RANGO = [8, 22]

const problema = ref({
  m: 3,
  n: 4,
  origenes: ['O1', 'O2', 'O3'],
  destinos: ['D1', 'D2', 'D3', 'D4'],
  costos: [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
  oferta: [0, 0, 0],
  demanda: [0, 0, 0, 0],
})

const opciones = reactive({
  metodo_inicial: 'vogel',
  modo: 'minimizar',
  criterio_entrada: 'mas_negativo',
  mostrar_procedimiento: false,
  mostrar_inicial: true,
  mostrar_potenciales: true,
  mostrar_costos_reducidos: true,
  mostrar_ciclo: true,
  mostrar_asignacion_por_iteracion: true,
  mostrar_sensibilidad: false,
  paso_a_paso: false,
  max_iteraciones: 100,
  decimales: 2,
})

const grilla = ref(null)
const resultado = ref(null)
const sensibilidad = ref(null)
const comparacion = ref(null)
const vistaIteracion = ref(0)
const pantalla = ref('datos') // 'datos' | 'resultado'
const pestana = ref('pasos')
// Opciones con las que se resolvió: la pantalla de resultado no debe cambiar si luego se editan.
const opcionesRes = ref(null)
let problemaRes = null
const estado = ref('Listo. Edita los datos y pulsa Resolver.')
const obsoleto = ref(false)
const loading = ref(false)
const tamanoTexto = ref(TAMANO_TEXTO_DEFECTO)

const estadoEsError = computed(() => /^(Error|No se pudo)/.test(estado.value))
const etiquetaMedida = computed(() => (opcionesRes.value?.modo === 'maximizar' ? 'Ganancia' : 'Costo'))
const mejoraTotal = computed(() => {
  const r = resultado.value
  if (!r) return 0
  return opcionesRes.value.modo === 'maximizar' ? r.costo - r.costo_inicial : r.costo_inicial - r.costo
})

let api = null
function esperarApi() {
  return new Promise((resolve) => {
    if (window.pywebview?.api) resolve(window.pywebview.api)
    else window.addEventListener('pywebviewready', () => resolve(window.pywebview.api), { once: true })
  })
}

async function cargarEjemplo() {
  const r = await api.ejemplo()
  if (r?.problema) problema.value = conDimensiones(r.problema)
}

function cambiarZoom(delta) {
  tamanoTexto.value =
    delta === 0
      ? TAMANO_TEXTO_DEFECTO
      : Math.max(TAMANO_TEXTO_RANGO[0], Math.min(TAMANO_TEXTO_RANGO[1], tamanoTexto.value + delta))
}

function manejarAtajos(e) {
  if (!(e.ctrlKey || e.metaKey)) return
  if (e.key === 'Enter') {
    e.preventDefault()
    if (pantalla.value === 'datos') resolverProblema()
  } else if (e.key.toLowerCase() === 'o') {
    e.preventDefault()
    abrir()
  } else if (e.key.toLowerCase() === 's') {
    e.preventDefault()
    guardar()
  } else if (e.key === '+' || e.key === '=') {
    e.preventDefault()
    cambiarZoom(1)
  } else if (e.key === '-') {
    e.preventDefault()
    cambiarZoom(-1)
  } else if (e.key === '0') {
    e.preventDefault()
    cambiarZoom(0)
  }
}

// El tamaño del texto escala con rem, así que basta cambiar el tamaño raíz.
// Se aplica como multiplicador sobre la escala fluida de style.css (no un px fijo).
watch(tamanoTexto, (t) => document.documentElement.style.setProperty('--text-zoom', t / TAMANO_TEXTO_DEFECTO))

onMounted(async () => {
  window.addEventListener('keydown', manejarAtajos)
  api = await esperarApi()
  await cargarEjemplo()
})
onUnmounted(() => {
  window.removeEventListener('keydown', manejarAtajos)
  // El zoom de MODI no debe seguir aplicado al volver al inicio u otro método
  document.documentElement.style.removeProperty('--text-zoom')
})

function marcarObsoleto() {
  if (resultado.value) obsoleto.value = true
}

// WebKitGTK's structuredClone() throws DataCloneError on Vue's reactive proxies;
// round-tripping through JSON strips the proxy and matches what the Api bridge needs anyway.
function clonarPlano(x) {
  return JSON.parse(JSON.stringify(x))
}

// El backend no envía m ni n; los componentes los usan para dimensionar tablas y diagramas.
function conDimensiones(p) {
  return { ...p, m: p.origenes.length, n: p.destinos.length }
}

const iteracionActual = computed(() => resultado.value?.historial[vistaIteracion.value] ?? null)

async function resolverProblema() {
  obsoleto.value = false
  loading.value = true
  try {
    const opcionesUsadas = { ...opciones }
    const r = await api.resolver(clonarPlano(problema.value), opcionesUsadas)
    if (r.error) {
      estado.value = `Error: ${r.error}`
      resultado.value = null
      return
    }
    resultado.value = { ...r, problema: conDimensiones(r.problema) }
    opcionesRes.value = opcionesUsadas
    problemaRes = clonarPlano(problema.value)
    pantalla.value = 'resultado'
    pestana.value = 'pasos'
    window.scrollTo(0, 0)
    vistaIteracion.value = 0
    sensibilidad.value = null
    comparacion.value = null
    estado.value = r.optimo
      ? `Solución óptima · ${r.mejoras} iteración(es) de mejora`
      : `No convergió en ${opciones.max_iteraciones} iteraciones`
    await Promise.all([cargarSensibilidad(), cargarComparacion()])
  } finally {
    loading.value = false
  }
}

async function cargarSensibilidad() {
  sensibilidad.value = await api.sensibilidad(problemaRes, opcionesRes.value)
}

async function cargarComparacion() {
  comparacion.value = await api.comparar(problemaRes, opcionesRes.value)
}

async function abrir() {
  const r = await api.abrir_problema()
  if (!r) return
  if (r.error) {
    estado.value = `No se pudo abrir: ${r.error}`
    return
  }
  problema.value = conDimensiones(r.problema)
  resultado.value = null
  pantalla.value = 'datos'
  estado.value = `Abierto: ${r.ruta}`
}

async function guardar() {
  const r = await api.guardar_problema(clonarPlano(problema.value))
  if (!r) return
  estado.value = r.error ? `No se pudo guardar: ${r.error}` : `Problema guardado en ${r.ruta}`
}

async function exportar() {
  if (!resultado.value) {
    estado.value = 'Primero resuelve un problema.'
    return
  }
  const r = await api.exportar_procedimiento(clonarPlano(problema.value), { ...opciones })
  if (!r) return
  estado.value = r.error ? `No se pudo exportar: ${r.error}` : `Procedimiento exportado a ${r.ruta}`
}

const PESTANAS = [
  { id: 'pasos', texto: 'Paso a paso' },
  { id: 'red', texto: 'Red' },
  { id: 'sensibilidad', texto: 'Sensibilidad' },
  { id: 'comparar', texto: 'Comparar métodos' },
]
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-app flex-col gap-4 bg-neutral-950 px-gutter py-4 text-neutral-100">
    <header class="flex flex-wrap items-baseline justify-between gap-x-4">
      <h1 class="text-xl font-semibold">Método MODI</h1>
      <p class="text-xs text-neutral-500">Ctrl+Enter resolver · Ctrl+O abrir · Ctrl+S guardar · Ctrl +/− tamaño del texto</p>
    </header>

    <!-- Pantalla 1: datos y opciones -->
    <main v-if="pantalla === 'datos'" class="flex flex-1 flex-col gap-4">
      <ResultBanner :estilo="estadoEsError ? 'aviso' : 'info'" :texto="obsoleto ? 'Los datos u opciones cambiaron desde el último resultado' : estado" />

      <div class="grid gap-4 lg:grid-cols-[1fr_22rem]">
        <section class="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
          <h2 class="font-semibold text-neutral-200">1. Problema</h2>
          <ProblemGrid ref="grilla" v-model="problema" @change="marcarObsoleto" />
          <div class="flex flex-wrap gap-2 pt-1 text-sm">
            <button type="button" class="rounded border border-neutral-700 px-3 py-1 hover:bg-neutral-800" @click="abrir">Abrir…</button>
            <button type="button" class="rounded border border-neutral-700 px-3 py-1 hover:bg-neutral-800" @click="guardar">Guardar…</button>
            <button type="button" class="rounded border border-neutral-700 px-3 py-1 hover:bg-neutral-800" @click="cargarEjemplo">Ejemplo</button>
          </div>
        </section>

        <div class="space-y-4">
          <section class="space-y-2 rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
            <h2 class="font-semibold text-neutral-200">2. Método</h2>
            <OptionsPanel v-model="opciones" />
          </section>
          <section class="space-y-2 rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
            <h2 class="font-semibold text-neutral-200">3. Procedimiento</h2>
            <ProcedureOptions v-model="opciones" />
          </section>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <button
          type="button"
          :disabled="loading"
          class="inline-flex min-w-64 flex-1 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-6 py-3 text-lg font-semibold hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-none"
          @click="resolverProblema"
        >
          <svg v-if="loading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z" />
          </svg>
          {{ loading ? 'Resolviendo…' : 'Resolver' }}
          <span v-if="!loading" class="font-normal text-indigo-200">(Ctrl+Enter)</span>
        </button>
        <button
          v-if="resultado" type="button"
          class="rounded-lg border border-neutral-700 px-4 py-3 text-neutral-300 hover:bg-neutral-800"
          @click="pantalla = 'resultado'"
        >Ver último resultado →</button>
      </div>
    </main>

    <!-- Pantalla 2: resultado y paso a paso -->
    <main v-else-if="resultado" class="flex flex-1 flex-col gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <button type="button" class="rounded-lg border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800" @click="pantalla = 'datos'">← Editar datos</button>
        <h2 class="text-lg font-semibold">Resultado</h2>
        <button type="button" class="ml-auto rounded-lg border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800" @click="exportar">Exportar…</button>
      </div>

      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div class="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
          <p class="text-xs text-neutral-500">{{ etiquetaMedida }} inicial</p>
          <p class="text-2xl font-semibold">{{ num(resultado.costo_inicial, opcionesRes.decimales) }}</p>
        </div>
        <div class="rounded-xl border border-indigo-700/60 bg-indigo-500/10 p-3">
          <p class="text-xs text-indigo-300">{{ etiquetaMedida }} final</p>
          <p class="text-2xl font-semibold text-indigo-100">{{ num(resultado.costo, opcionesRes.decimales) }}</p>
        </div>
        <div class="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
          <p class="text-xs text-neutral-500">{{ opcionesRes.modo === 'maximizar' ? 'Mejora' : 'Ahorro' }}</p>
          <p class="text-2xl font-semibold" :class="mejoraTotal > 0 ? 'text-emerald-300' : ''">{{ num(mejoraTotal, opcionesRes.decimales) }}</p>
        </div>
        <div class="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
          <p class="text-xs text-neutral-500">Iteraciones de mejora</p>
          <p class="text-2xl font-semibold">{{ resultado.mejoras }}</p>
        </div>
      </div>

      <div class="flex flex-wrap gap-1 border-b border-neutral-800 text-sm">
        <button
          v-for="p in PESTANAS" :key="p.id" type="button"
          class="px-3 py-1.5"
          :class="pestana === p.id ? 'border-b-2 border-indigo-500 text-indigo-300' : 'text-neutral-400 hover:text-neutral-200'"
          @click="pestana = p.id"
        >{{ p.texto }}</button>
      </div>

      <PasosView v-if="pestana === 'pasos'" :resultado="resultado" :opciones="opcionesRes" />

      <template v-else-if="pestana === 'red'">
        <label class="flex items-center gap-2 text-sm">
          Vista:
          <select v-model.number="vistaIteracion" class="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5">
            <option v-for="(titulo, k) in resultado.titulos" :key="k" :value="k">{{ titulo }}</option>
          </select>
        </label>
        <div class="h-[70vh]">
          <NetworkDiagram
            :problema="resultado.problema" :iteracion="iteracionActual" :decimales="opcionesRes.decimales"
            :titulo="resultado.titulos[vistaIteracion]"
          />
        </div>
      </template>
      <SensitivityTable
        v-else-if="pestana === 'sensibilidad'"
        :filas="sensibilidad?.filas ?? []" :decimales="opcionesRes.decimales" :error="sensibilidad?.error ?? ''"
      />
      <ComparisonTable v-else-if="pestana === 'comparar'" :filas="comparacion?.filas ?? []" :decimales="opcionesRes.decimales" />
    </main>
  </div>
</template>
