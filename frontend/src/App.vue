<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import ComparisonTable from './components/ComparisonTable.vue'
import NetworkDiagram from './components/NetworkDiagram.vue'
import OptionsPanel from './components/OptionsPanel.vue'
import ProblemGrid from './components/ProblemGrid.vue'
import ProcedureOptions from './components/ProcedureOptions.vue'
import ReportView from './components/ReportView.vue'
import ResultBanner from './components/ResultBanner.vue'
import SensitivityTable from './components/SensitivityTable.vue'
import TableDiagram from './components/TableDiagram.vue'

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
const pestana = ref('procedimiento')
const estado = ref('Listo. Edita los datos y pulsa Resolver.')
const obsoleto = ref(false)
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
  <div class="flex min-h-screen flex-col gap-3 bg-neutral-950 p-4 text-neutral-100 lg:h-screen">
    <div class="flex flex-wrap items-baseline justify-between gap-x-4">
      <h1 class="text-xl font-semibold">OptiLab — Método MODI</h1>
      <p class="text-xs text-neutral-500">Ctrl+Enter resolver · Ctrl+O abrir · Ctrl+S guardar · Ctrl +/− tamaño del texto</p>
    </div>

    <div class="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[fit-content(540px)_1fr] lg:overflow-hidden">
      <div class="flex flex-col lg:overflow-hidden">
        <div class="flex-1 space-y-4 pr-1 lg:overflow-y-auto">
          <section class="space-y-2 rounded border border-neutral-800 p-3">
            <h2 class="text-sm font-semibold text-neutral-300">Problema</h2>
            <ProblemGrid ref="grilla" v-model="problema" @change="marcarObsoleto" />
            <div class="flex flex-wrap gap-2 pt-1 text-xs">
              <button type="button" class="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800" @click="abrir">Abrir…</button>
              <button type="button" class="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800" @click="guardar">Guardar…</button>
              <button type="button" class="rounded border border-neutral-700 px-2 py-1 hover:bg-neutral-800" @click="cargarEjemplo">Ejemplo</button>
            </div>
          </section>

          <section class="space-y-2 rounded border border-neutral-800 p-3">
            <h2 class="text-sm font-semibold text-neutral-300">Método</h2>
            <OptionsPanel v-model="opciones" />
          </section>

          <section class="space-y-2 rounded border border-neutral-800 p-3">
            <h2 class="text-sm font-semibold text-neutral-300">Procedimiento</h2>
            <ProcedureOptions v-model="opciones" />
          </section>
        </div>

        <button
          type="button"
          class="mt-3 w-full shrink-0 rounded bg-indigo-600 px-4 py-2 font-medium hover:bg-indigo-500"
          @click="resolverProblema"
        >
          Resolver <span class="font-normal text-indigo-200">(Ctrl+Enter)</span>
        </button>
      </div>

      <div class="flex min-h-[70vh] flex-col lg:min-h-0 lg:overflow-hidden">
        <div class="mb-2 flex items-center gap-3 text-sm">
          <label v-if="resultado" class="flex items-center gap-2">
            Vista:
            <select v-model.number="vistaIteracion" class="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5">
              <option v-for="(titulo, k) in resultado.titulos" :key="k" :value="k">{{ titulo }}</option>
            </select>
          </label>
          <button type="button" class="ml-auto rounded border border-neutral-700 px-2 py-1 text-xs hover:bg-neutral-800" @click="exportar">
            Exportar…
          </button>
        </div>

        <ResultBanner :estilo="bannerEstilo" :texto="bannerTexto" />

        <div class="mb-2 flex flex-wrap gap-1 border-b border-neutral-800 text-sm">
          <button
            v-for="p in PESTANAS" :key="p.id" type="button"
            class="px-3 py-1.5"
            :class="pestana === p.id ? 'border-b-2 border-indigo-500 text-indigo-300' : 'text-neutral-400 hover:text-neutral-200'"
            @click="pestana = p.id"
          >{{ p.texto }}</button>
        </div>

        <div class="flex-1 overflow-hidden">
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
      </div>
    </div>
  </div>
</template>
