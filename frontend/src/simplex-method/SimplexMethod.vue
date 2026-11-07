<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchExamples, solveSimplexProblem, analyzeContext, DEFAULT_EXAMPLES } from './api.js'

// --- State ---
const examples = ref(DEFAULT_EXAMPLES)
const activeTab = ref('editor') // 'editor' | 'steps' | 'results'
const displayMode = ref('frac') // 'frac' | 'dec'
const isLoading = ref(false)
const isAnalyzing = ref(false)
const errorMessage = ref('')
const copySuccess = ref(false)

// Context & Problem Statement
const problemTitle = ref('Fabricación de Mesas y Sillas')
const contextStatement = ref(
  'Una fábrica produce mesas (x1) y sillas (x2). Cada mesa vendida aporta una ganancia de $3 y cada silla $5. El taller dispone de hasta 4 horas para corte de piezas, 12 horas en el área de ensamblaje y 18 horas para acabado final. ¿Cuántas mesas y sillas se deben fabricar para maximizar la ganancia total del taller?'
)
const objectiveName = ref('Ganancia total del taller')
const objectiveUnit = ref('$')
const varDescriptions = ref(['Mesas a fabricar', 'Sillas a fabricar'])
const varUnits = ref(['mesas', 'sillas'])
const constraintDescriptions = ref([
  'Horas disponibles en Corte',
  'Horas disponibles en Ensamblaje',
  'Horas disponibles en Acabado',
])
const constraintUnits = ref(['horas', 'horas', 'horas'])
const showContextDetails = ref(true)

// Problem definition
const objective = ref('max') // 'max' | 'min'
const varNames = ref(['x1', 'x2'])
const objCoeffs = ref(['3', '5'])
const constraints = ref([
  { lhs: ['1', '0'], sign: '<=', rhs: '4' },
  { lhs: ['0', '2'], sign: '<=', rhs: '12' },
  { lhs: ['3', '2'], sign: '<=', rhs: '18' },
])

// Solution result
const solution = ref(null)
const currentStepIdx = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(2000)
let playTimer = null

// --- Lifecycle ---
onMounted(async () => {
  try {
    const loadedExamples = await fetchExamples()
    if (loadedExamples && loadedExamples.length) {
      examples.value = loadedExamples
    }
  } catch (e) {
    console.warn('Usando ejemplos por defecto:', e)
  }
})

onUnmounted(() => {
  stopPlayback()
})

// --- Context Analyzer Helper ---
async function handleAnalyzeContext() {
  if (!contextStatement.value.trim()) {
    errorMessage.value = 'Por favor escribe o pega el enunciado del problema antes de analizar.'
    return
  }
  isAnalyzing.value = true
  errorMessage.value = ''
  try {
    const analysis = await analyzeContext(contextStatement.value)
    if (analysis) {
      if (analysis.objective) objective.value = analysis.objective
      if (analysis.objective_name) objectiveName.value = analysis.objective_name
      if (analysis.objective_unit) objectiveUnit.value = analysis.objective_unit

      if (analysis.suggested_vars && analysis.suggested_vars.length > 0) {
        analysis.suggested_vars.forEach((name, i) => {
          if (i < varDescriptions.value.length) {
            varDescriptions.value[i] = name
          }
        })
      }

      if (analysis.suggested_constraints && analysis.suggested_constraints.length > 0) {
        analysis.suggested_constraints.forEach((name, i) => {
          if (i < constraintDescriptions.value.length) {
            constraintDescriptions.value[i] = name
          }
        })
      }
    }
  } catch (e) {
    console.error('Error al analizar contexto:', e)
    errorMessage.value = 'No se pudo analizar el contexto automáticamente.'
  } finally {
    isAnalyzing.value = false
  }
}

// Copy conclusion text to clipboard
async function copyConclusionText() {
  const conc = solution.value?.final_report?.contextual_conclusion
  if (!conc) return

  let text = `========================================================\n`
  text += `${conc.headline}\n`
  text += `========================================================\n\n`
  if (contextStatement.value) {
    text += `ENUNCIADO / CONTEXTO:\n${contextStatement.value}\n\n`
  }
  text += `RESUMEN EJECUTIVO:\n${conc.executive_summary}\n\n`
  text += `VALOR ÓPTIMO ALCANZADO:\n${conc.optimal_value_text} (${conc.optimal_value_dec})\n\n`

  if (conc.plan_of_action && conc.plan_of_action.length) {
    text += `PLAN DE ACCIÓN RECOMENDADO:\n`
    conc.plan_of_action.forEach((p) => {
      text += `• ${p.action_text}\n`
    })
    text += `\n`
  }

  if (conc.resource_diagnosis && conc.resource_diagnosis.length) {
    text += `DIAGNÓSTICO DE RECURSOS:\n`
    conc.resource_diagnosis.forEach((r) => {
      text += `• ${r.description} (${r.constraint}): ${r.status_title}. ${r.detail}\n`
    })
    text += `\n`
  }

  if (conc.sensitivity_insights && conc.sensitivity_insights.length) {
    text += `RECOMENDACIONES ECONÓMICAS (PRECIOS SOMBRA):\n`
    conc.sensitivity_insights.forEach((s) => {
      text += `• ${s.description} (Precio sombra = ${s.shadow_price} ${s.unit}): ${s.recommendation}\n`
    })
  }

  try {
    await navigator.clipboard.writeText(text)
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2500)
  } catch (err) {
    console.error('Error al copiar:', err)
  }
}

// --- Editor Helpers ---
function loadExample(ex) {
  objective.value = ex.objective || 'max'
  varNames.value = [...(ex.var_names || ['x1', 'x2'])]
  objCoeffs.value = ex.c.map(String)
  constraints.value = ex.constraints.map((r) => ({
    lhs: r.lhs.map(String),
    sign: r.sign || '<=',
    rhs: String(r.rhs),
  }))

  const ctx = ex.context || {}
  problemTitle.value = ctx.title || ex.title || 'Ejercicio Simplex'
  contextStatement.value = ctx.statement || ex.description || ''
  objectiveName.value = ctx.objective_name || (ex.objective === 'max' ? 'Ganancia total' : 'Costo total')
  objectiveUnit.value = ctx.objective_unit || '$'

  varDescriptions.value = ctx.var_descriptions
    ? [...ctx.var_descriptions]
    : varNames.value.map((v) => `Variable ${v}`)
  varUnits.value = ctx.var_units
    ? [...ctx.var_units]
    : varNames.value.map(() => 'unidades')

  constraintDescriptions.value = ctx.constraint_descriptions
    ? [...ctx.constraint_descriptions]
    : constraints.value.map((_, i) => `Restricción R${i + 1}`)
  constraintUnits.value = ctx.constraint_units
    ? [...ctx.constraint_units]
    : constraints.value.map(() => 'horas')

  solution.value = null
  currentStepIdx.value = 0
  activeTab.value = 'editor'
  errorMessage.value = ''
}

function addVariable() {
  const nextNum = varNames.value.length + 1
  const newName = `x${nextNum}`
  varNames.value.push(newName)
  objCoeffs.value.push('0')
  varDescriptions.value.push(`Variable ${newName}`)
  varUnits.value.push('unidades')
  constraints.value.forEach((r) => r.lhs.push('0'))
}

function removeVariable() {
  if (varNames.value.length <= 1) return
  varNames.value.pop()
  objCoeffs.value.pop()
  varDescriptions.value.pop()
  varUnits.value.pop()
  constraints.value.forEach((r) => r.lhs.pop())
}

function addConstraint() {
  const newLhs = Array.from({ length: varNames.value.length }, () => '0')
  const newIdx = constraints.value.length + 1
  constraints.value.push({
    lhs: newLhs,
    sign: '<=',
    rhs: '0',
  })
  constraintDescriptions.value.push(`Restricción R${newIdx}`)
  constraintUnits.value.push('unidades')
}

function removeConstraint(idx) {
  if (constraints.value.length <= 1) return
  constraints.value.splice(idx, 1)
  constraintDescriptions.value.splice(idx, 1)
  constraintUnits.value.splice(idx, 1)
}

function resetProblem() {
  objective.value = 'max'
  varNames.value = ['x1', 'x2']
  objCoeffs.value = ['0', '0']
  varDescriptions.value = ['Variable x1', 'Variable x2']
  varUnits.value = ['unidades', 'unidades']
  constraints.value = [{ lhs: ['0', '0'], sign: '<=', rhs: '0' }]
  constraintDescriptions.value = ['Restricción R1']
  constraintUnits.value = ['unidades']
  problemTitle.value = 'Nuevo Problema de Optimización'
  contextStatement.value = ''
  objectiveName.value = 'Función Objetivo'
  objectiveUnit.value = '$'
  solution.value = null
  errorMessage.value = ''
}

function scrollToMathSection() {
  const el = document.getElementById('math-definition-card')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

// Format mathematical expression for preview
const objectivePreview = computed(() => {
  const parts = []
  varNames.value.forEach((name, i) => {
    const val = objCoeffs.value[i] || '0'
    if (val !== '0') {
      const isNeg = val.startsWith('-')
      const absVal = isNeg ? val.slice(1) : val
      const term = absVal === '1' ? name : `${absVal}${name}`
      if (parts.length === 0) {
        parts.push(isNeg ? `-${term}` : term)
      } else {
        parts.push(isNeg ? `- ${term}` : `+ ${term}`)
      }
    }
  })
  const expr = parts.length > 0 ? parts.join(' ') : '0'
  return `${objective.value.toUpperCase()} Z = ${expr}`
})

// --- Solver trigger ---
async function handleSolve() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const problem = {
      objective: objective.value,
      c: objCoeffs.value,
      var_names: varNames.value,
      constraints: constraints.value.map((r) => ({
        lhs: r.lhs,
        sign: r.sign,
        rhs: r.rhs,
      })),
      context: {
        title: problemTitle.value || 'Ejercicio de Optimización',
        statement: contextStatement.value,
        objective_name: objectiveName.value || 'Función Objetivo Z',
        objective_unit: objectiveUnit.value || '$',
        var_descriptions: varDescriptions.value,
        var_units: varUnits.value,
        constraint_descriptions: constraintDescriptions.value,
        constraint_units: constraintUnits.value,
      },
      max_iterations: 100,
    }

    const res = await solveSimplexProblem(problem)
    solution.value = res
    currentStepIdx.value = 0
    activeTab.value = 'steps'
  } catch (err) {
    errorMessage.value = err.message || 'Error al resolver el modelo simplex.'
  } finally {
    isLoading.value = false
  }
}

// --- Step Stepper & Playback ---
const currentStep = computed(() => {
  if (!solution.value || !solution.value.steps || solution.value.steps.length === 0) {
    return null
  }
  return solution.value.steps[currentStepIdx.value] || null
})

const totalSteps = computed(() => {
  return solution.value?.steps?.length || 0
})

function goToStep(idx) {
  if (idx >= 0 && idx < totalSteps.value) {
    currentStepIdx.value = idx
  }
}

function prevStep() {
  if (currentStepIdx.value > 0) {
    currentStepIdx.value--
  }
}

function nextStep() {
  if (currentStepIdx.value < totalSteps.value - 1) {
    currentStepIdx.value++
  } else {
    stopPlayback()
  }
}

function togglePlayback() {
  if (isPlaying.value) {
    stopPlayback()
  } else {
    startPlayback()
  }
}

function startPlayback() {
  isPlaying.value = true
  if (currentStepIdx.value >= totalSteps.value - 1) {
    currentStepIdx.value = 0
  }
  playTimer = setInterval(() => {
    if (currentStepIdx.value < totalSteps.value - 1) {
      currentStepIdx.value++
    } else {
      stopPlayback()
    }
  }, playSpeed.value)
}

function stopPlayback() {
  isPlaying.value = false
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

// Cell value formatter
function formatCell(cell) {
  if (!cell) return '-'
  if (typeof cell === 'string' || typeof cell === 'number') return cell
  return displayMode.value === 'frac' ? cell.frac : cell.dec
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shadow-lg shadow-black/20">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-400 flex items-center justify-center font-bold text-xl text-white shadow-md shadow-indigo-500/25">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
            <polyline points="16 7 22 7 22 13"/>
          </svg>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-bold tracking-tight text-white">OptiLab</h1>
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-medium border border-indigo-500/20">
              Método Simplex
            </span>
          </div>
          <p class="text-xs text-slate-400">Paso a paso con tablas, pivotes y análisis contextualizado</p>
        </div>
      </div>

      <!-- Navigation Tabs & Display Mode -->
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          <button
            @click="activeTab = 'editor'"
            :class="[
              'px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all cursor-pointer flex items-center gap-2',
              activeTab === 'editor'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            ]"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              <path d="m15 5 4 4"/>
            </svg>
            <span>Configurar Modelo</span>
          </button>
          <button
            @click="activeTab = 'steps'"
            :disabled="!solution"
            :class="[
              'px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all cursor-pointer flex items-center gap-2',
              activeTab === 'steps'
                ? 'bg-indigo-600 text-white shadow-sm'
                : solution
                  ? 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                  : 'text-slate-600 cursor-not-allowed opacity-50'
            ]"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/>
            </svg>
            <span>Tablas Paso a Paso {{ solution ? `(${solution.steps.length})` : '' }}</span>
          </button>
          <button
            @click="activeTab = 'results'"
            :disabled="!solution"
            :class="[
              'px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all cursor-pointer flex items-center gap-2',
              activeTab === 'results'
                ? 'bg-indigo-600 text-white shadow-sm'
                : solution
                  ? 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                  : 'text-slate-600 cursor-not-allowed opacity-50'
            ]"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
            <span>Informe Final</span>
          </button>
        </div>

        <!-- Format Switch (Fraction vs Decimal) -->
        <div class="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 text-xs">
          <button
            @click="displayMode = 'frac'"
            :class="[
              'px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer',
              displayMode === 'frac' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            ]"
            title="Mostrar números en fracciones exactas (ej. 3/2)"
          >
            Fracciones (a/b)
          </button>
          <button
            @click="displayMode = 'dec'"
            :class="[
              'px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer',
              displayMode === 'dec' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            ]"
            title="Mostrar números en formato decimal (ej. 1.5000)"
          >
            Decimales (0.0)
          </button>
        </div>
      </div>
    </header>

    <!-- Error Alert Banner -->
    <div v-if="errorMessage" class="bg-rose-500/10 border-b border-rose-500/30 px-6 py-3 text-rose-300 flex items-center justify-between text-sm">
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-rose-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="text-rose-400 hover:text-rose-200 text-xs font-semibold cursor-pointer flex items-center gap-1">
        <span>Cerrar</span>
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- Main Workspace -->
    <main class="flex-1 p-4 md:p-6 max-w-7xl w-full mx-auto space-y-6">

      <!-- =================================================================== -->
      <!-- TAB 1: MODEL CONFIGURATION / EDITOR -->
      <!-- =================================================================== -->
      <div v-show="activeTab === 'editor'" class="space-y-6">

        <!-- Quick Preset Examples -->
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <svg class="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <span>Ejemplos Prácticos Listos para Usar</span>
            </h2>
            <span class="text-xs text-slate-500">Haz clic en cualquier caso para cargarlo</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            <button
              v-for="ex in examples"
              :key="ex.id"
              @click="loadExample(ex)"
              class="text-left p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-800/80 hover:border-indigo-500/50 transition-all group cursor-pointer"
            >
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors">
                  {{ ex.title }}
                </span>
                <svg class="w-4 h-4 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </div>
              <p class="text-xs text-slate-400 mt-1 line-clamp-1">
                {{ ex.description }}
              </p>
            </button>
          </div>
        </div>

        <!-- Problem Statement & Context Card (STEP 1: BEFORE EXERCISE) -->
        <div class="bg-slate-900/70 border border-indigo-500/30 rounded-2xl p-6 shadow-xl space-y-5">
          <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <line x1="10" y1="9" x2="8" y2="9"/>
                </svg>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="text-base font-bold text-white">
                    Paso 1: Contexto y Enunciado del Problema
                  </h2>
                  <span class="text-[11px] px-2.5 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20 font-semibold">
                    Antes de Iniciar el Ejercicio
                  </span>
                </div>
                <p class="text-xs text-slate-400">
                  Ingresa el contexto real para interpretar la solución, los cuellos de botella y la conclusión gerencial
                </p>
              </div>
            </div>

            <!-- Actions inside header -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                @click="handleAnalyzeContext"
                :disabled="isAnalyzing || !contextStatement.trim()"
                class="px-3.5 py-1.5 rounded-xl bg-violet-600/25 text-violet-300 border border-violet-500/40 text-xs font-semibold hover:bg-violet-600/40 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                title="Analiza el texto para detectar Maximizar/Minimizar, variables y unidades"
              >
                <svg v-if="isAnalyzing" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m15 4-2 4 4 2-4 2 2 4-4-2-2 4-2-4-4 2 2-4-4-2 4-2-2-4 4 2 2-4 2 4 4-2Z"/>
                </svg>
                <span>{{ isAnalyzing ? 'Analizando...' : 'Auto-detectar Contexto' }}</span>
              </button>
            </div>
          </div>

          <!-- Problem Title Input -->
          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-slate-300 block">
              Título o Identificador del Ejercicio:
            </label>
            <input
              v-model="problemTitle"
              type="text"
              placeholder="Ej. Planificación de Producción - Mesas y Sillas"
              class="w-full px-3.5 py-2 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <!-- Statement Textarea -->
          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Enunciado Completo del Problema / Caso Real:</span>
              <span class="text-[11px] text-slate-500">Pega aquí el problema antes de formular las ecuaciones</span>
            </label>
            <textarea
              v-model="contextStatement"
              rows="3"
              class="w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none leading-relaxed resize-y"
              placeholder="Ejemplo: Una empresa fabrica mesas (x1) y sillas (x2). Cada mesa deja una utilidad de $3 y cada silla $5. Las horas de corte disponibles son 4, ensamble 12 y acabado 18..."
            ></textarea>
          </div>

          <!-- Context Parameters Accordion / Grid -->
          <div class="space-y-3 pt-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/>
                  <path d="M7 7h.01"/>
                </svg>
                <span>Variables, Unidades y Significado del Negocio</span>
              </span>
              <button
                type="button"
                @click="showContextDetails = !showContextDetails"
                class="text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer flex items-center gap-1"
              >
                <span>{{ showContextDetails ? 'Ocultar detalles' : 'Personalizar nombres y unidades' }}</span>
                <svg v-if="showContextDetails" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="18 15 12 9 6 15"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>

            <div v-show="showContextDetails" class="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80 space-y-4">
              <!-- Objective Definition in Context -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-medium text-slate-400 block mb-1">
                    ¿Qué representa la Función Objetivo (Z)?
                  </label>
                  <input
                    v-model="objectiveName"
                    type="text"
                    placeholder="Ej. Ganancia total del taller, Costo de operación"
                    class="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label class="text-xs font-medium text-slate-400 block mb-1">
                    Unidad de Medida de Z
                  </label>
                  <input
                    v-model="objectiveUnit"
                    type="text"
                    placeholder="Ej. $, USD, EUR, horas, unidades"
                    class="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-emerald-400 font-mono font-bold focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <!-- Variables Meanings -->
              <div class="space-y-2 pt-2 border-t border-slate-800">
                <span class="text-xs font-semibold text-slate-300 block">
                  Significado de cada Variable de Decisión:
                </span>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  <div
                    v-for="(name, idx) in varNames"
                    :key="'var-desc-' + idx"
                    class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 space-y-1.5"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-xs font-bold text-indigo-400 font-mono">{{ name }}</span>
                      <span class="text-[10px] text-slate-500">Variable {{ idx + 1 }}</span>
                    </div>
                    <input
                      v-model="varDescriptions[idx]"
                      type="text"
                      placeholder="Ej. Mesas a fabricar"
                      class="w-full px-2 py-1 bg-slate-950 border border-slate-700/80 rounded text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                    />
                    <div class="flex items-center gap-1.5">
                      <span class="text-[10px] text-slate-400">Unidad:</span>
                      <input
                        v-model="varUnits[idx]"
                        type="text"
                        placeholder="Ej. mesas, unidades"
                        class="w-full px-2 py-0.5 bg-slate-950 border border-slate-700/80 rounded text-[11px] text-slate-300 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Constraints Meanings -->
              <div class="space-y-2 pt-2 border-t border-slate-800">
                <span class="text-xs font-semibold text-slate-300 block">
                  Recurso o significado de cada Restricción:
                </span>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                  <div
                    v-for="(r, rIdx) in constraints"
                    :key="'c-desc-' + rIdx"
                    class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 space-y-1.5"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-xs font-bold text-slate-400 font-mono">R{{ rIdx + 1 }}</span>
                      <span class="text-[10px] text-slate-500">{{ r.sign }} {{ r.rhs }}</span>
                    </div>
                    <input
                      v-model="constraintDescriptions[rIdx]"
                      type="text"
                      placeholder="Ej. Horas de corte en taller"
                      class="w-full px-2 py-1 bg-slate-950 border border-slate-700/80 rounded text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                    />
                    <div class="flex items-center gap-1.5">
                      <span class="text-[10px] text-slate-400">Unidad:</span>
                      <input
                        v-model="constraintUnits[rIdx]"
                        type="text"
                        placeholder="Ej. horas, kg, unidades"
                        class="w-full px-2 py-0.5 bg-slate-950 border border-slate-700/80 rounded text-[11px] text-slate-300 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom helper bar to continue to formulation -->
          <div class="pt-1 flex items-center justify-between text-xs text-slate-400">
            <span>El contexto se guardará automáticamente junto con el modelo.</span>
            <button
              type="button"
              @click="scrollToMathSection"
              class="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <span>Continuar a las Ecuaciones</span>
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Problem Input Card (STEP 2: MATHEMATICAL FORMULATION) -->
        <div id="math-definition-card" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="4" y1="21" x2="4" y2="14"/>
                  <line x1="4" y1="10" x2="4" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12" y2="3"/>
                  <line x1="20" y1="21" x2="20" y2="16"/>
                  <line x1="20" y1="12" x2="20" y2="3"/>
                  <line x1="1" y1="14" x2="7" y2="14"/>
                  <line x1="9" y1="8" x2="15" y2="8"/>
                  <line x1="17" y1="16" x2="23" y2="16"/>
                </svg>
              </div>
              <div>
                <h2 class="text-base font-bold text-white">
                  Paso 2: Definición del Modelo Matemático
                </h2>
                <p class="text-xs text-slate-400">Coeficientes de la función objetivo y restricciones lineales</p>
              </div>
            </div>

            <!-- Variable Counters -->
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-400 mr-1">Variables:</span>
              <button
                @click="removeVariable"
                :disabled="varNames.length <= 1"
                class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-bold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                title="Quitar variable"
              >
                -
              </button>
              <span class="text-sm font-bold text-indigo-400 px-1">{{ varNames.length }}</span>
              <button
                @click="addVariable"
                class="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-bold hover:bg-slate-700 cursor-pointer"
                title="Agregar variable"
              >
                +
              </button>
            </div>
          </div>

          <!-- Objective Function Input -->
          <div class="space-y-3 bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <label class="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <circle cx="12" cy="12" r="6"/>
                  <circle cx="12" cy="12" r="2"/>
                </svg>
                <span>Sentido y Coeficientes de la Función Objetivo</span>
              </label>

              <!-- Maximize / Minimize Toggle -->
              <div class="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-700 text-xs">
                <button
                  type="button"
                  @click="objective = 'max'"
                  :class="[
                    'px-3 py-1 rounded-md font-semibold transition-all cursor-pointer',
                    objective === 'max' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  ]"
                >
                  MAXIMIZAR
                </button>
                <button
                  type="button"
                  @click="objective = 'min'"
                  :class="[
                    'px-3 py-1 rounded-md font-semibold transition-all cursor-pointer',
                    objective === 'min' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
                  ]"
                >
                  MINIMIZAR
                </button>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3 pt-2">
              <span class="text-sm font-bold text-indigo-400 min-w-16">
                {{ objective.toUpperCase() }} Z =
              </span>

              <div
                v-for="(name, idx) in varNames"
                :key="'obj-' + idx"
                class="flex items-center gap-1.5"
              >
                <input
                  v-model="objCoeffs[idx]"
                  type="text"
                  class="w-20 px-2.5 py-1.5 text-center bg-slate-900 border border-slate-700 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  placeholder="0"
                />
                <span class="text-sm font-semibold text-slate-300">{{ name }}</span>
                <span v-if="idx < varNames.length - 1" class="text-slate-600 font-bold ml-1">+</span>
              </div>
            </div>
          </div>

          <!-- Constraints List Input -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                  <polyline points="2 17 12 22 22 17"/>
                  <polyline points="2 12 12 17 22 12"/>
                </svg>
                <span>Restricciones del Sistema ({{ constraints.length }})</span>
              </label>

              <button
                @click="addConstraint"
                class="px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 text-xs font-semibold hover:bg-indigo-600/30 transition-all flex items-center gap-1 cursor-pointer"
              >
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                <span>Agregar Restricción</span>
              </button>
            </div>

            <div class="space-y-2.5">
              <div
                v-for="(r, rIdx) in constraints"
                :key="'row-' + rIdx"
                class="flex flex-wrap items-center gap-3 bg-slate-950/40 p-3 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors"
              >
                <span class="text-xs font-bold text-slate-400 min-w-8">
                  R{{ rIdx + 1 }}:
                </span>

                <!-- Coefficients per variable -->
                <div class="flex flex-wrap items-center gap-2">
                  <div
                    v-for="(name, cIdx) in varNames"
                    :key="'r-' + rIdx + '-c-' + cIdx"
                    class="flex items-center gap-1"
                  >
                    <input
                      v-model="r.lhs[cIdx]"
                      type="text"
                      class="w-18 px-2 py-1.5 text-center bg-slate-900 border border-slate-700 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
                      placeholder="0"
                    />
                    <span class="text-xs text-slate-400">{{ name }}</span>
                    <span v-if="cIdx < varNames.length - 1" class="text-slate-600 font-bold ml-0.5">+</span>
                  </div>
                </div>

                <!-- Sign Operator -->
                <select
                  v-model="r.sign"
                  class="bg-slate-900 border border-slate-700 text-slate-200 text-sm font-bold rounded-lg px-2 py-1.5 focus:border-indigo-500 focus:outline-none cursor-pointer"
                >
                  <option value="<=">&le; (Menor o igual)</option>
                  <option value=">=">&ge; (Mayor o igual)</option>
                  <option value="=">= (Igualdad)</option>
                </select>

                <!-- RHS Value -->
                <input
                  v-model="r.rhs"
                  type="text"
                  class="w-20 px-2 py-1.5 text-center bg-slate-900 border border-slate-700 rounded-lg text-sm text-emerald-400 font-mono font-bold focus:border-indigo-500 focus:outline-none"
                  placeholder="b"
                  title="Lado derecho (b)"
                />

                <!-- Delete Button -->
                <button
                  @click="removeConstraint(rIdx)"
                  :disabled="constraints.length <= 1"
                  class="text-slate-500 hover:text-rose-400 text-sm p-1 ml-auto disabled:opacity-20 disabled:cursor-not-allowed cursor-pointer"
                  title="Eliminar esta restricción"
                >
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Non-negativity condition note -->
            <div class="text-xs text-slate-400 pt-1 flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>Condición de no negatividad: {{ varNames.join(', ') }} &ge; 0</span>
            </div>
          </div>

          <!-- Mathematical Formula Live Preview -->
          <div class="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-4 space-y-1.5 font-mono text-sm">
            <div class="text-xs uppercase font-semibold text-indigo-400 tracking-wider">
              Vista Previa del Modelo Matemático
            </div>
            <div class="text-slate-200 font-semibold">{{ objectivePreview }}</div>
            <div class="text-xs text-slate-400">sujeto a:</div>
            <div v-for="(r, idx) in constraints" :key="'preview-' + idx" class="text-xs text-slate-300">
              R{{ idx + 1 }}:
              <span v-for="(c, cIdx) in r.lhs" :key="cIdx">
                <span v-if="cIdx > 0"> + </span>
                {{ c }}{{ varNames[cIdx] }}
              </span>
              {{ r.sign }} {{ r.rhs }}
            </div>
            <div class="text-xs text-slate-400">{{ varNames.join(', ') }} &ge; 0</div>
          </div>

          <!-- Action Buttons -->
          <div class="flex items-center justify-between pt-2">
            <button
              @click="resetProblem"
              class="px-4 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm font-medium hover:bg-slate-800 transition-colors cursor-pointer flex items-center gap-2"
            >
              <svg class="w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M8 16H3v5"/>
              </svg>
              <span>Limpiar Todo</span>
            </button>

            <button
              @click="handleSolve"
              :disabled="isLoading"
              class="px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-base shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2.5 cursor-pointer disabled:opacity-50"
            >
              <svg v-if="isLoading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              <span>{{ isLoading ? 'Resolviendo...' : 'Resolver Método Simplex' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- =================================================================== -->
      <!-- TAB 2: STEP-BY-STEP TABLEAUS (PASO A PASO) -->
      <!-- =================================================================== -->
      <div v-show="activeTab === 'steps'" class="space-y-6">
        <div v-if="!solution" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <p class="text-lg font-medium text-slate-300">No hay ninguna solución activa.</p>
          <p class="text-sm mt-1">Configura un modelo en la primera pestaña y presiona "Resolver".</p>
          <button
            @click="activeTab = 'editor'"
            class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500 cursor-pointer inline-flex items-center gap-2"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              <path d="m15 5 4 4"/>
            </svg>
            <span>Ir al Editor</span>
          </button>
        </div>

        <div v-else class="space-y-6">
          <!-- Stepper Controls Bar -->
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-4">
            <!-- Navigation Buttons -->
            <div class="flex items-center gap-1.5">
              <button
                @click="goToStep(0)"
                :disabled="currentStepIdx === 0"
                class="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                title="Primera tabla (Tabla 0)"
              >
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="11 19 2 12 11 5 11 19"/>
                  <polygon points="22 19 13 12 22 5 22 19"/>
                </svg>
                <span>Inicio</span>
              </button>
              <button
                @click="prevStep"
                :disabled="currentStepIdx === 0"
                class="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                title="Paso anterior"
              >
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                <span>Anterior</span>
              </button>
              <button
                @click="togglePlayback"
                class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-sm cursor-pointer flex items-center gap-1.5"
              >
                <svg v-if="isPlaying" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="6" y="4" width="4" height="16"/>
                  <rect x="14" y="4" width="4" height="16"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <span>{{ isPlaying ? 'Pausar' : 'Auto' }}</span>
              </button>
              <button
                @click="nextStep"
                :disabled="currentStepIdx >= totalSteps - 1"
                class="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                title="Siguiente paso"
              >
                <span>Siguiente</span>
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
              <button
                @click="goToStep(totalSteps - 1)"
                :disabled="currentStepIdx >= totalSteps - 1"
                class="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                title="Última tabla"
              >
                <span>Fin</span>
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 19 22 12 13 5 13 19"/>
                  <polygon points="2 19 11 12 2 5 2 19"/>
                </svg>
              </button>
            </div>

            <!-- Current Step Indicator -->
            <div class="text-center">
              <span class="text-xs text-slate-400 font-medium">
                Paso <strong class="text-indigo-400">{{ currentStepIdx + 1 }}</strong> de <strong class="text-slate-200">{{ totalSteps }}</strong>
              </span>
              <div class="text-sm font-bold text-white">
                {{ currentStep?.title }}
              </div>
            </div>

            <!-- Jump to Tab / Pills -->
            <div class="flex items-center gap-1 flex-wrap">
              <button
                v-for="(st, idx) in solution.steps"
                :key="'step-pill-' + idx"
                @click="goToStep(idx)"
                :class="[
                  'px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer',
                  currentStepIdx === idx
                    ? 'bg-indigo-600 text-white shadow-sm ring-2 ring-indigo-400/30'
                    : 'bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700'
                ]"
              >
                T{{ idx }}
              </button>
            </div>
          </div>

          <!-- Tableau Card -->
          <div v-if="currentStep" class="bg-slate-900/70 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <!-- Table Header Bar -->
            <div class="bg-slate-800/60 px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect width="18" height="18" x="3" y="3" rx="2"/>
                  <path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/>
                </svg>
                <span class="font-bold text-slate-100 text-sm">
                  Matriz Simplex — {{ currentStep.title }}
                </span>
                <span v-if="currentStep.phase" class="text-xs px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-semibold border border-violet-500/30">
                  Fase {{ currentStep.phase }}
                </span>
              </div>

              <!-- Badges for Pivot Details -->
              <div v-if="currentStep.pivot" class="flex items-center gap-2 text-xs flex-wrap">
                <span class="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold">
                  Entra: {{ currentStep.pivot.entering_var }}
                </span>
                <span class="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">
                  Sale: {{ currentStep.pivot.leaving_var }}
                </span>
                <span class="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  Pivote: {{ currentStep.pivot.pivot_val }} ({{ currentStep.pivot.pivot_row_label }}, {{ currentStep.pivot.entering_var }})
                </span>
              </div>
              <div v-else-if="currentStep.status === 'optimal'" class="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span>Solución Óptima</span>
              </div>
            </div>

            <!-- Table View -->
            <div class="overflow-x-auto p-4">
              <table class="w-full text-center border-collapse">
                <thead>
                  <tr class="border-b border-slate-800 text-xs font-semibold uppercase text-slate-400">
                    <th class="py-2.5 px-3 bg-slate-950/40 text-left">Fila</th>
                    <th class="py-2.5 px-3 bg-slate-950/40">Base</th>
                    <th
                      v-for="(col, cIdx) in currentStep.col_names"
                      :key="'hdr-' + cIdx"
                      :class="[
                        'py-2.5 px-3 font-mono transition-colors',
                        currentStep.pivot && currentStep.pivot.entering_col === cIdx
                          ? 'bg-cyan-500/15 text-cyan-300 border-x border-cyan-500/30 font-bold'
                          : ''
                      ]"
                    >
                      {{ col }}
                    </th>
                    <th class="py-2.5 px-4 bg-slate-950/40 font-bold text-slate-300">
                      B (Lado Der.)
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/80 text-sm font-mono">
                  <tr
                    v-for="(row, rIdx) in currentStep.rows"
                    :key="'row-data-' + rIdx"
                    :class="[
                      'transition-colors',
                      rIdx === 0 ? 'bg-indigo-950/20 font-semibold' : '',
                      currentStep.pivot && currentStep.pivot.leaving_row === rIdx
                        ? 'bg-amber-500/10 border-y border-amber-500/30'
                        : 'hover:bg-slate-800/30'
                    ]"
                  >
                    <!-- Row Label -->
                    <td class="py-2.5 px-3 text-left font-bold text-slate-400 text-xs">
                      {{ row.row_label }}
                    </td>

                    <!-- Basic Variable -->
                    <td class="py-2.5 px-3 font-bold text-indigo-300">
                      {{ row.base_var }}
                    </td>

                    <!-- Cells -->
                    <td
                      v-for="(cell, cIdx) in row.cells.slice(0, currentStep.col_names.length)"
                      :key="'cell-' + rIdx + '-' + cIdx"
                      :class="[
                        'py-2.5 px-3 transition-all',
                        currentStep.pivot && currentStep.pivot.entering_col === cIdx
                          ? 'bg-cyan-500/10'
                          : '',
                        currentStep.pivot && currentStep.pivot.leaving_row === rIdx && currentStep.pivot.entering_col === cIdx
                          ? 'bg-amber-500/30 ring-2 ring-amber-400 font-extrabold text-amber-200 rounded'
                          : 'text-slate-200'
                      ]"
                    >
                      <span v-if="currentStep.pivot && currentStep.pivot.leaving_row === rIdx && currentStep.pivot.entering_col === cIdx">
                        [{{ formatCell(cell) }}]
                      </span>
                      <span v-else>
                        {{ formatCell(cell) }}
                      </span>
                    </td>

                    <!-- RHS (B) -->
                    <td class="py-2.5 px-4 font-bold text-emerald-400 bg-slate-950/30">
                      {{ formatCell(row.rhs) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Table Legend / Footnote -->
            <div class="px-5 py-2.5 bg-slate-950/60 border-t border-slate-800 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-4">
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded bg-cyan-500/30 border border-cyan-500"></span>
                  Columna entrante (Bland)
                </span>
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded bg-amber-500/30 border border-amber-500"></span>
                  Fila saliente (Cociente mín.)
                </span>
                <span class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded bg-amber-400 font-bold text-black text-[9px] flex items-center justify-center">P</span>
                  Elemento Pivote
                </span>
              </div>
              <div class="text-slate-300">
                Valor actual de {{ currentStep.z_label }} = <strong class="text-emerald-400">{{ formatCell(currentStep.z_val) }}</strong>
              </div>
            </div>
          </div>

          <!-- Educational Details for Current Step -->
          <div v-if="currentStep" class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- 1. Optimality Analysis -->
            <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                <svg class="w-4 h-4 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <span>1. Prueba de Optimalidad (Fila F0)</span>
              </h3>
              <p class="text-xs text-slate-300 leading-relaxed">
                {{ currentStep.optimality_check.explanation }}
              </p>

              <div v-if="currentStep.optimality_check.candidates && currentStep.optimality_check.candidates.length" class="space-y-1.5 pt-2 border-t border-slate-800">
                <span class="text-xs text-slate-400 font-semibold">Coeficientes en F0:</span>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="cand in currentStep.optimality_check.candidates"
                    :key="cand.var"
                    :class="[
                      'px-2 py-0.5 rounded text-xs font-mono font-bold',
                      currentStep.pivot && currentStep.pivot.entering_var === cand.var
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                        : 'bg-slate-800 text-slate-300'
                    ]"
                  >
                    {{ cand.var }} = {{ cand.val }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 2. Minimum Ratio Test -->
            <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                <svg class="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="6" r="1.5"/><line x1="5" y1="12" x2="19" y2="12"/><circle cx="12" cy="18" r="1.5"/>
                </svg>
                <span>2. Prueba del Cociente Mínimo (B / a)</span>
              </h3>

              <div v-if="currentStep.pivot && currentStep.pivot.ratios" class="space-y-2">
                <p class="text-xs text-slate-300">
                  Calculamos B &divide; entrada para cada restricción donde entrada &gt; 0:
                </p>

                <div class="space-y-1 text-xs font-mono max-h-48 overflow-y-auto pr-1">
                  <div
                    v-for="r in currentStep.pivot.ratios"
                    :key="'ratio-' + r.row"
                    :class="[
                      'p-2 rounded-lg border text-xs',
                      r.valid && currentStep.pivot.leaving_row === r.row
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-200 font-bold'
                        : r.valid
                          ? 'bg-slate-950/40 border-slate-800 text-slate-300'
                          : 'bg-slate-950/20 border-slate-900 text-slate-500 line-through opacity-70'
                    ]"
                  >
                    <div class="flex justify-between">
                      <span>F{{ r.row }} ({{ r.base_var }}):</span>
                      <span>{{ r.note }}</span>
                    </div>
                  </div>
                </div>

                <div v-if="currentStep.pivot.tie_explanation" class="text-xs text-amber-300 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
                  {{ currentStep.pivot.tie_explanation }}
                </div>
              </div>
              <div v-else class="text-xs text-slate-400">
                No hay prueba de cocientes para esta tabla.
              </div>
            </div>

            <!-- 3. Row Operations / Gauss-Jordan -->
            <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                <svg class="w-4 h-4 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>
                  <path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/>
                </svg>
                <span>3. Operaciones de Fila (Gauss-Jordan)</span>
              </h3>

              <div v-if="currentStep.pivot && currentStep.pivot.row_operations" class="space-y-2 text-xs font-mono max-h-60 overflow-y-auto pr-1">
                <div
                  v-for="(op, opIdx) in currentStep.pivot.row_operations"
                  :key="'op-' + opIdx"
                  class="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 space-y-1"
                >
                  <div class="font-bold text-indigo-300 flex items-center justify-between">
                    <span>{{ op.formula }}</span>
                    <span class="text-[10px] text-slate-400 uppercase">{{ op.type }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-slate-400">
                La tabla no requiere operaciones de pivoteo adicionales.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- =================================================================== -->
      <!-- TAB 3: FINAL REPORT & POST-OPTIMAL ANALYSIS -->
      <!-- =================================================================== -->
      <div v-show="activeTab === 'results'" class="space-y-6">
        <div v-if="!solution || !solution.final_report" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <p class="text-lg font-medium text-slate-300">Aún no se ha calculado el informe final.</p>
          <button
            @click="activeTab = 'editor'"
            class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500 cursor-pointer inline-flex items-center gap-2"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              <path d="m15 5 4 4"/>
            </svg>
            <span>Configurar y Resolver</span>
          </button>
        </div>

        <div v-else class="space-y-6">
          <!-- ========================================================= -->
          <!-- CONTEXTUAL CONCLUSION SHOWCASE CARD                       -->
          <!-- ========================================================= -->
          <div
            v-if="solution.final_report && solution.final_report.contextual_conclusion"
            class="bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl space-y-6"
          >
            <!-- Header bar with copy button -->
            <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-indigo-500/20">
              <div class="flex items-center gap-3">
                <div class="h-11 w-11 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-lg shadow-indigo-600/40">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="6"/>
                    <circle cx="12" cy="12" r="2"/>
                  </svg>
                </div>
                <div>
                  <div class="flex items-center gap-2 flex-wrap">
                    <h2 class="text-lg font-extrabold text-white">
                      {{ solution.final_report.contextual_conclusion.headline }}
                    </h2>
                    <span class="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                      Conclusión del Ejercicio
                    </span>
                  </div>
                  <p class="text-xs text-slate-400 mt-0.5">
                    Respuesta gerencial y técnica redactada con base en el contexto del problema planteado
                  </p>
                </div>
              </div>

              <!-- Copy to clipboard button -->
              <button
                type="button"
                @click="copyConclusionText"
                class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition-all flex items-center gap-2 cursor-pointer shadow-sm active:scale-95"
                title="Copiar texto de la conclusión completa al portapapeles"
              >
                <svg v-if="copySuccess" class="w-4 h-4 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else class="w-4 h-4 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
                  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                </svg>
                <span>{{ copySuccess ? '¡Conclusión Copiada!' : 'Copiar Conclusión' }}</span>
              </button>
            </div>

            <!-- Executive Summary text block -->
            <div class="bg-indigo-950/50 border border-indigo-500/30 rounded-xl p-4.5 space-y-2">
              <span class="text-xs uppercase font-bold tracking-wider text-indigo-400 flex items-center gap-1.5">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                  <rect width="20" height="14" x="2" y="6" rx="2"/>
                </svg>
                <span>Resumen Ejecutivo de la Decisión:</span>
              </span>
              <p class="text-sm md:text-base text-slate-100 font-medium leading-relaxed">
                {{ solution.final_report.contextual_conclusion.executive_summary }}
              </p>
            </div>

            <!-- Plan of Action Variable Cards -->
            <div
              v-if="solution.final_report.contextual_conclusion.plan_of_action && solution.final_report.contextual_conclusion.plan_of_action.length"
              class="space-y-3"
            >
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m7.5 4.27 9 5.15"/>
                  <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
                  <path d="m3.3 7 8.7 5 8.7-5"/>
                  <path d="M12 22V12"/>
                </svg>
                <span>Plan de Acción Específico por Variable</span>
              </h3>

              <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                <div
                  v-for="(p, pIdx) in solution.final_report.contextual_conclusion.plan_of_action"
                  :key="'plan-act-' + pIdx"
                  class="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-indigo-500/40 transition-colors"
                >
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-indigo-400 font-mono">{{ p.var }}</span>
                    <span class="text-xs font-semibold text-slate-400">{{ p.unit }}</span>
                  </div>
                  <div class="text-sm font-bold text-slate-200">
                    {{ p.description }}
                  </div>
                  <div class="flex items-baseline gap-2 pt-1">
                    <span class="text-2xl font-extrabold text-white font-mono">
                      {{ displayMode === 'frac' ? p.value_frac : p.value_dec }}
                    </span>
                    <span class="text-xs font-semibold text-indigo-300">{{ p.unit }}</span>
                  </div>
                  <p class="text-xs text-slate-400 pt-1 border-t border-slate-900 leading-normal">
                    {{ p.action_text }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Resource Diagnosis (Cuellos de Botella vs Holguras) -->
            <div
              v-if="solution.final_report.contextual_conclusion.resource_diagnosis && solution.final_report.contextual_conclusion.resource_diagnosis.length"
              class="space-y-3"
            >
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                  <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                  <path d="M7 21h10"/><path d="M12 3v18"/>
                </svg>
                <span>Diagnóstico de Recursos: Cuellos de Botella y Holguras</span>
              </h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div
                  v-for="(rd, rdIdx) in solution.final_report.contextual_conclusion.resource_diagnosis"
                  :key="'r-diag-' + rdIdx"
                  :class="[
                    'p-4 rounded-xl border space-y-2 transition-colors',
                    rd.is_active
                      ? 'bg-rose-950/20 border-rose-500/30'
                      : 'bg-emerald-950/20 border-emerald-500/30'
                  ]"
                >
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-xs font-bold text-slate-300">
                      {{ rd.constraint }}: {{ rd.description }}
                    </span>
                    <span
                      :class="[
                        'text-[11px] px-2.5 py-0.5 rounded font-bold uppercase flex items-center gap-1.5',
                        rd.is_active
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      ]"
                    >
                      <span :class="['w-2 h-2 rounded-full', rd.is_active ? 'bg-rose-400' : 'bg-emerald-400']"></span>
                      <span>{{ rd.is_active ? 'Cuello de Botella' : 'Con Holgura' }}</span>
                    </span>
                  </div>
                  <div class="text-xs font-semibold text-slate-200">
                    {{ rd.status_title }}
                  </div>
                  <p class="text-xs text-slate-400 leading-relaxed">
                    {{ rd.detail }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Sensitivity Recommendations -->
            <div
              v-if="solution.final_report.contextual_conclusion.sensitivity_insights && solution.final_report.contextual_conclusion.sensitivity_insights.length"
              class="space-y-3"
            >
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                  <polyline points="16 7 22 7 22 13"/>
                </svg>
                <span>Recomendaciones de Gestión Basadas en Precios Sombra</span>
              </h3>

              <div class="space-y-2">
                <div
                  v-for="(sens, sIdx) in solution.final_report.contextual_conclusion.sensitivity_insights"
                  :key="'sens-' + sIdx"
                  class="bg-slate-950/50 border border-slate-800 p-3 rounded-xl flex items-start gap-3"
                >
                  <div class="h-8 w-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>
                      <path d="M9 18h6"/><path d="M10 22h4"/>
                    </svg>
                  </div>
                  <div class="space-y-0.5 text-xs">
                    <span class="font-bold text-slate-200">
                      {{ sens.description }} ({{ sens.constraint }}) &bull; Precio sombra: <strong class="text-emerald-400 font-mono">{{ sens.shadow_price }} {{ sens.unit }}</strong>
                    </span>
                    <p class="text-slate-400 leading-relaxed">
                      {{ sens.recommendation }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Status Banner -->
          <div
            :class="[
              'p-6 rounded-2xl border shadow-xl flex items-center justify-between flex-wrap gap-4',
              solution.status === 'optimal'
                ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200'
                : solution.status === 'unbounded'
                  ? 'bg-amber-950/30 border-amber-500/30 text-amber-200'
                  : 'bg-rose-950/30 border-rose-500/30 text-rose-200'
            ]"
          >
            <div>
              <div class="flex items-center gap-2.5">
                <svg v-if="solution.status === 'optimal'" class="w-6 h-6 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="9 12 11 14 15 10"/>
                </svg>
                <svg v-else-if="solution.status === 'unbounded'" class="w-6 h-6 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <svg v-else class="w-6 h-6 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <h2 class="text-xl font-bold tracking-tight">
                  {{ solution.status === 'optimal' ? 'Solución Óptima Encontrada' : solution.status === 'unbounded' ? 'Problema No Acotado (Unbounded)' : 'Problema Infáctible' }}
                </h2>
              </div>
              <p class="text-xs text-slate-300 mt-1">
                {{ solution.final_report.message || 'El algoritmo simplex ha completado todas las iteraciones necesarias.' }}
              </p>
            </div>

            <!-- Optimal Value Display -->
            <div v-if="solution.status === 'optimal'" class="bg-emerald-900/40 px-5 py-3 rounded-xl border border-emerald-500/40 text-center">
              <span class="text-xs font-semibold uppercase tracking-wider text-emerald-300 block">
                Valor Óptimo Z*
              </span>
              <span class="text-2xl font-extrabold text-white font-mono">
                {{ formatCell(solution.final_report.z_optimal) }}
              </span>
            </div>
          </div>

          <!-- Decision Variables Values -->
          <div v-if="solution.status === 'optimal'" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 class="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>Valores Óptimos de las Variables de Decisión</span>
            </h3>

            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <div
                v-for="(val, name) in solution.final_report.variables"
                :key="'opt-var-' + name"
                class="bg-slate-950/60 border border-slate-800 p-4 rounded-xl text-center hover:border-indigo-500/40 transition-colors"
              >
                <span class="text-xs font-semibold text-slate-400 block">{{ name }}</span>
                <span class="text-lg font-bold text-indigo-300 font-mono mt-1 block">
                  {{ formatCell(val) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Verification by Substitution in Original Constraints -->
          <div v-if="solution.status === 'optimal' && solution.final_report.substitutions" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 class="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
                <polyline points="9 12 11 14 15 10"/>
              </svg>
              <span>Verificación por Sustitución en Restricciones Originales</span>
            </h3>

            <div class="space-y-2.5">
              <div
                v-for="sub in solution.final_report.substitutions"
                :key="'sub-' + sub.index"
                class="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl flex flex-wrap items-center justify-between gap-3 font-mono text-xs"
              >
                <div class="flex items-center gap-2">
                  <svg v-if="sub.satisfied" class="w-4 h-4 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <svg v-else class="w-4 h-4 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  <span class="font-bold text-slate-300">{{ sub.label }}:</span>
                  <span class="text-slate-200">{{ sub.expression }}</span>
                </div>

                <div class="flex items-center gap-2">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded text-[11px] font-semibold',
                      sub.is_active
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-slate-800 text-slate-300'
                    ]"
                  >
                    {{ sub.status_text }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Sensitivity Analysis / Shadow Prices -->
          <div v-if="solution.status === 'optimal' && solution.final_report.shadow_prices && solution.final_report.shadow_prices.length" class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 class="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                <polyline points="16 7 22 7 22 13"/>
              </svg>
              <span>Análisis de Sensibilidad y Precios Sombra</span>
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                v-for="sp in solution.final_report.shadow_prices"
                :key="sp.constraint"
                class="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-1.5"
              >
                <div class="flex justify-between items-center">
                  <span class="text-xs font-bold text-slate-300">{{ sp.constraint }}</span>
                  <span class="text-sm font-bold text-emerald-400 font-mono">
                    Precio Sombra: {{ sp.price }}
                  </span>
                </div>
                <p class="text-xs text-slate-400 leading-relaxed">
                  {{ sp.interpretation }}
                </p>
              </div>
            </div>
          </div>

          <!-- Additional Analysis (Degeneracy, Alternative Optima) -->
          <div v-if="solution.status === 'optimal'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
              <h4 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="6" y1="3" x2="6" y2="15"/>
                  <circle cx="18" cy="6" r="3"/>
                  <circle cx="6" cy="18" r="3"/>
                  <path d="M18 9a9 9 0 0 1-9 9"/>
                </svg>
                <span>Óptimos Alternativos</span>
              </h4>
              <p class="text-xs text-slate-300 leading-relaxed">
                {{ solution.final_report.alternative_optima?.message }}
              </p>
            </div>

            <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-2">
              <h4 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                  <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                  <path d="M7 21h10"/><path d="M12 3v18"/>
                </svg>
                <span>Análisis de Degeneración</span>
              </h4>
              <p class="text-xs text-slate-300 leading-relaxed">
                {{ solution.final_report.degeneracy?.message }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
      OptiLab &bull; Herramienta de Optimización Lineal y Método Simplex &bull; pywebview + Vue 3 + Tailwind
    </footer>
  </div>
</template>
