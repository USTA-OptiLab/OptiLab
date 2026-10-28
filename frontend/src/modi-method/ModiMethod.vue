<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import ComparisonTable from './ComparisonTable.vue'
import NetworkDiagram from './NetworkDiagram.vue'
import OptionsPanel from './OptionsPanel.vue'
import ProblemGrid from './ProblemGrid.vue'
import ProcedureOptions from './ProcedureOptions.vue'
import ReportView from './ReportView.vue'
import ResultBanner from './ResultBanner.vue'
import SensitivityTable from './SensitivityTable.vue'
import TableDiagram from './TableDiagram.vue'

const TAMANO_TEXTO_DEFECTO = 12
const TAMANO_TEXTO_RANGO = [8, 22]

const secondaryButtonClass =
  'rounded-lg border border-neutral-700 px-3 py-2 text-xs font-medium text-neutral-300 transition hover:border-neutral-600 hover:text-white'

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
const pestana = ref('procedimiento')
const estado = ref('Listo. Edita los datos y pulsa Resolver.')
const obsoleto = ref(false)
const loading = ref(false)
const tamanoTexto = ref(TAMANO_TEXTO_DEFECTO)

const bannerEstilo = computed(() => {
  if (obsoleto.value) return 'aviso'
  if (!resultado.value) return 'info'
  return resultado.value.optimo ? 'ok' : 'aviso'
})
const bannerTexto = computed(() =>
  obsoleto.value ? 'Los datos u opciones cambiaron: pulsa Resolver para actualizar el resultado' : estado.value,
)

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
    resolverProblema()
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

onMounted(async () => {
  window.addEventListener('keydown', manejarAtajos)
  api = await esperarApi()
  await cargarEjemplo()
})
onUnmounted(() => window.removeEventListener('keydown', manejarAtajos))

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
    const r = await api.resolver(clonarPlano(problema.value), { ...opciones })
    if (r.error) {
      estado.value = `Error: ${r.error}`
      resultado.value = null
      return
    }
    resultado.value = { ...r, problema: conDimensiones(r.problema) }
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
  sensibilidad.value = await api.sensibilidad(clonarPlano(problema.value), { ...opciones })
}

async function cargarComparacion() {
  comparacion.value = await api.comparar(clonarPlano(problema.value), { ...opciones })
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
  { id: 'procedimiento', texto: 'Procedimiento' },
  { id: 'tabla', texto: 'Tabla' },
  { id: 'red', texto: 'Red' },
  { id: 'sensibilidad', texto: 'Sensibilidad' },
  { id: 'comparar', texto: 'Comparar métodos' },
]
</script>

<template>
  <div class="min-h-screen bg-neutral-950 text-neutral-100">
    <header class="border-b border-neutral-800 bg-neutral-950/90">
      <div
        class="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8"
      >
        <div class="flex items-center gap-3">
          <div
            class="grid h-10 w-10 place-items-center rounded-xl bg-indigo-500/15 ring-1 ring-inset ring-indigo-500/30"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              class="h-5 w-5 text-indigo-300"
            >
              <circle cx="5" cy="6" r="2" />
              <circle cx="5" cy="18" r="2" />
              <circle cx="19" cy="12" r="2" />
              <path d="M7 6.8 17 11M7 17.2 17 12.8" stroke-linecap="round" />
            </svg>
          </div>
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.22em] text-indigo-300">
              OptiLab
            </p>
            <h1 class="text-xl font-semibold tracking-tight">Método MODI</h1>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span
            class="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs text-neutral-400"
          >
            Problema de transporte · distribución modificada
          </span>
          <span class="text-[11px] text-neutral-500">
            Ctrl+Enter resolver · Ctrl+O abrir · Ctrl+S guardar · Ctrl +/− tamaño del texto
          </span>
        </div>
      </div>
    </header>

    <main
      class="mx-auto grid max-w-[1600px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[fit-content(560px)_minmax(0,1fr)] lg:px-8"
    >
      <aside class="flex flex-col gap-4 lg:sticky lg:top-6 lg:max-h-[calc(100vh-7rem)] lg:self-start">
        <div class="flex-1 space-y-4 pr-1 lg:overflow-y-auto">
          <section
            class="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-4 shadow-lg shadow-black/20"
          >
            <h2 class="text-sm font-semibold text-neutral-100">Problema</h2>
            <div class="mt-3">
              <ProblemGrid ref="grilla" v-model="problema" @change="marcarObsoleto" />
            </div>
            <div class="mt-3 grid grid-cols-3 gap-2">
              <button type="button" :class="secondaryButtonClass" @click="abrir">Abrir…</button>
              <button type="button" :class="secondaryButtonClass" @click="guardar">Guardar…</button>
              <button type="button" :class="secondaryButtonClass" @click="cargarEjemplo">Ejemplo</button>
            </div>
          </section>

          <section
            class="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-4 shadow-lg shadow-black/20"
          >
            <h2 class="text-sm font-semibold text-neutral-100">Método</h2>
            <div class="mt-3">
              <OptionsPanel v-model="opciones" />
            </div>
          </section>

          <section
            class="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-4 shadow-lg shadow-black/20"
          >
            <h2 class="text-sm font-semibold text-neutral-100">Procedimiento</h2>
            <div class="mt-3">
              <ProcedureOptions v-model="opciones" />
            </div>
          </section>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-950/40 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
          @click="resolverProblema"
        >
          <svg v-if="loading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z" />
          </svg>
          {{ loading ? 'Resolviendo…' : 'Resolver' }}
          <span v-if="!loading" class="font-normal text-indigo-200">(Ctrl+Enter)</span>
        </button>
      </aside>

      <section class="flex min-h-[70vh] flex-col lg:min-h-0">
        <div class="mb-3 flex flex-wrap items-center gap-3 text-sm">
          <label v-if="resultado" class="flex items-center gap-2">
            Vista:
            <select
              v-model.number="vistaIteracion"
              class="rounded-md border border-neutral-700 bg-neutral-950 px-2 py-1 text-sm text-neutral-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            >
              <option v-for="(titulo, k) in resultado.titulos" :key="k" :value="k">{{ titulo }}</option>
            </select>
          </label>
          <button type="button" class="ml-auto" :class="secondaryButtonClass" @click="exportar">
            Exportar…
          </button>
        </div>

        <ResultBanner :estilo="bannerEstilo" :texto="bannerTexto" />

        <div class="my-3 flex flex-wrap gap-2">
          <button
            v-for="p in PESTANAS"
            :key="p.id"
            type="button"
            class="rounded-lg border px-3 py-1.5 text-sm font-medium transition"
            :class="
              pestana === p.id
                ? 'border-indigo-500 bg-indigo-500/15 text-indigo-200'
                : 'border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200'
            "
            @click="pestana = p.id"
          >
            {{ p.texto }}
          </button>
        </div>

        <section
          class="flex-1 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-lg shadow-black/20"
        >
          <div class="h-full overflow-auto p-4">
            <ReportView
              v-if="pestana === 'procedimiento'"
              :bloques="resultado?.bloques ?? []" :paso-a-paso="opciones.paso_a_paso" :tamano-texto="tamanoTexto"
            />
            <TableDiagram
              v-else-if="pestana === 'tabla' && iteracionActual"
              :problema="resultado.problema" :iteracion="iteracionActual" :decimales="opciones.decimales"
              :titulo="resultado.titulos[vistaIteracion]"
            />
            <NetworkDiagram
              v-else-if="pestana === 'red' && iteracionActual"
              :problema="resultado.problema" :iteracion="iteracionActual" :decimales="opciones.decimales"
              :titulo="resultado.titulos[vistaIteracion]"
            />
            <SensitivityTable
              v-else-if="pestana === 'sensibilidad'"
              :filas="sensibilidad?.filas ?? []" :decimales="opciones.decimales" :error="sensibilidad?.error ?? ''"
            />
            <ComparisonTable v-else-if="pestana === 'comparar'" :filas="comparacion?.filas ?? []" :decimales="opciones.decimales" />
            <p v-else class="text-neutral-500">Resuelve un problema para ver esta vista.</p>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>
