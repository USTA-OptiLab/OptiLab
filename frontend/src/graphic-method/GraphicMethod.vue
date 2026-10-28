<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import FeasibleChart from './FeasibleChart.vue'
import { OP_OPTIONS, formatConstraint, formatNumber, formatTerms } from './format'

const fieldClass =
  'min-w-0 rounded-md border border-neutral-700 bg-neutral-950 px-2.5 py-1.5 font-mono text-sm text-neutral-100 outline-none transition placeholder:text-neutral-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20'
const selectClass =
  'rounded-md border border-neutral-700 bg-neutral-950 px-2 py-1.5 font-mono text-sm text-neutral-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20'

const sense = ref('max')
const c1 = ref(3)
const c2 = ref(2)
const constraints = ref([{ a1: 2, a2: 3, op: '<=', b: 12 }])

const result = ref(null)
const error = ref('')
const loading = ref(false)
const showObjective = ref(true)
const bridgeReady = ref(false)

const objectivePreview = computed(() => {
  const empty = [c1.value, c2.value].some(
    (value) => value === null || value === undefined || String(value).trim() === '',
  )
  if (empty) return 'Completa los coeficientes de Z'
  return `${sense.value === 'max' ? 'Max' : 'Min'} Z = ${formatTerms(c1.value, c2.value)}`
})

const constraintPreviews = computed(() =>
  constraints.value.map((constraint) => formatConstraint(constraint)),
)

const multipleOptima = computed(() => (result.value?.optimal_points?.length ?? 0) > 1)

const statusTitle = computed(() => {
  if (result.value?.status === 'optimal') return 'Solución óptima factible'
  if (result.value?.status === 'unbounded') return 'Función objetivo no acotada'
  return 'No existe región factible'
})

const statusMessage = computed(() => {
  if (result.value?.status === 'unbounded') {
    const verb = result.value.objective.sense === 'max' ? 'crecer' : 'disminuir'
    return `La función objetivo puede ${verb} indefinidamente dentro de la región factible, por lo que no existe un valor óptimo finito.`
  }
  if (result.value?.status === 'infeasible') {
    return 'Ningún punto del primer cuadrante satisface todas las restricciones al mismo tiempo.'
  }
  return ''
})

const statusClasses = computed(() => {
  if (result.value?.status === 'optimal') return 'border-emerald-500/30 bg-emerald-500/10'
  if (result.value?.status === 'unbounded') return 'border-amber-500/30 bg-amber-500/10'
  return 'border-rose-500/30 bg-rose-500/10'
})

const regionNote = computed(() => {
  if (!result.value) return ''
  if (result.value.status === 'infeasible') return 'No hay una región factible que sombrear.'
  if (!result.value.region.bounded) {
    return 'La región factible es no acotada; la vista se recorta hasta el borde del gráfico.'
  }
  return 'La región factible está sombreada en verde y los puntos no factibles se muestran atenuados.'
})

function addConstraint() {
  constraints.value.push({ a1: '', a2: '', op: '<=', b: '' })
}

function removeConstraint(index) {
  if (constraints.value.length > 1) constraints.value.splice(index, 1)
}

function loadExample() {
  sense.value = 'max'
  c1.value = 3
  c2.value = 2
  constraints.value = [
    { a1: 2, a2: 1, op: '<=', b: 18 },
    { a1: 2, a2: 3, op: '<=', b: 42 },
    { a1: 3, a2: 1, op: '<=', b: 24 },
  ]
  result.value = null
  error.value = ''
}

function clearForm() {
  sense.value = 'max'
  c1.value = ''
  c2.value = ''
  constraints.value = [{ a1: '', a2: '', op: '<=', b: '' }]
  result.value = null
  error.value = ''
}

function rowClass(point) {
  if (point.optimal) return 'bg-emerald-500/10 text-emerald-50'
  if (!point.feasible) return 'text-neutral-500'
  return 'text-neutral-200'
}

function pointState(point) {
  if (point.optimal) return 'Óptimo'
  if (point.feasible) return 'Vértice factible'
  return 'Descartado'
}

function pointStateClass(point) {
  if (point.optimal) {
    return 'inline-flex items-center gap-1 rounded-full bg-emerald-400/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-200 ring-1 ring-inset ring-emerald-400/30'
  }
  if (point.feasible) return 'text-[10px] font-medium text-sky-200'
  return 'text-[10px] text-neutral-600'
}

function validateFields() {
  const values = [
    c1.value,
    c2.value,
    ...constraints.value.flatMap((constraint) => [
      constraint.a1,
      constraint.a2,
      constraint.b,
    ]),
  ]
  return values.every(
    (value) =>
      value !== null &&
      value !== undefined &&
      String(value).trim() !== '' &&
      Number.isFinite(Number(value)),
  )
}

async function resolveProblem() {
  error.value = ''
  if (!validateFields()) {
    error.value = 'Completa todos los campos numéricos con valores válidos.'
    return
  }
  if (!bridgeReady.value) {
    error.value =
      'El motor Python no está disponible. Abre este módulo con pywebview: python -m optilab.graphic_method.'
    return
  }

  loading.value = true
  try {
    const payload = {
      sense: sense.value,
      objective: { c1: Number(c1.value), c2: Number(c2.value) },
      constraints: constraints.value.map((constraint) => ({
        a1: Number(constraint.a1),
        a2: Number(constraint.a2),
        op: constraint.op,
        b: Number(constraint.b),
      })),
    }
    const response = await window.pywebview.api.solve_graphical(payload)
    if (!response?.ok) {
      result.value = null
      error.value = response?.error ?? 'No se pudo resolver el problema.'
      return
    }
    result.value = response
  } catch (cause) {
    result.value = null
    error.value = `No se pudo resolver el problema: ${cause?.message ?? cause}`
  } finally {
    loading.value = false
  }
}

function checkBridge() {
  bridgeReady.value = Boolean(window.pywebview?.api?.solve_graphical)
}

onMounted(() => {
  checkBridge()
  window.addEventListener('pywebviewready', checkBridge)
})

onBeforeUnmount(() => {
  window.removeEventListener('pywebviewready', checkBridge)
})
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
              <path
                d="M4 19 19 4M4 19h16M7 15l3-3 3 2 6-6"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.22em] text-indigo-300">
              OptiLab
            </p>
            <h1 class="text-xl font-semibold tracking-tight">Método gráfico</h1>
          </div>
        </div>
        <span
          class="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs text-neutral-400"
        >
          Programación lineal · 2 variables
        </span>
      </div>
    </header>

    <main
      class="mx-auto grid max-w-[1600px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[390px_minmax(0,1fr)] lg:px-8"
    >
      <aside class="space-y-4 lg:sticky lg:top-6 lg:self-start">
        <form class="space-y-4" @submit.prevent="resolveProblem">
          <section
            class="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-4 shadow-lg shadow-black/20"
          >
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-semibold text-neutral-100">Función objetivo</h2>
              <span
                class="rounded-full bg-neutral-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-neutral-400"
              >
                Z
              </span>
            </div>

            <div class="mt-3 grid grid-cols-2 gap-2">
              <button
                type="button"
                class="rounded-lg border px-3 py-2 text-sm font-medium transition"
                :class="
                  sense === 'max'
                    ? 'border-indigo-500 bg-indigo-500/15 text-indigo-200'
                    : 'border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200'
                "
                @click="sense = 'max'"
              >
                Maximizar
              </button>
              <button
                type="button"
                class="rounded-lg border px-3 py-2 text-sm font-medium transition"
                :class="
                  sense === 'min'
                    ? 'border-indigo-500 bg-indigo-500/15 text-indigo-200'
                    : 'border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200'
                "
                @click="sense = 'min'"
              >
                Minimizar
              </button>
            </div>

            <div class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950/70 p-3">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-mono text-sm text-neutral-400">Z =</span>
                <input
                  v-model="c1"
                  type="number"
                  step="any"
                  placeholder="c₁"
                  class="w-20"
                  :class="fieldClass"
                />
                <span class="font-mono text-sm text-neutral-300">x₁ +</span>
                <input
                  v-model="c2"
                  type="number"
                  step="any"
                  placeholder="c₂"
                  class="w-20"
                  :class="fieldClass"
                />
                <span class="font-mono text-sm text-neutral-300">x₂</span>
              </div>
              <p class="mt-2 font-mono text-xs text-indigo-300">{{ objectivePreview }}</p>
            </div>
          </section>

          <section
            class="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-4 shadow-lg shadow-black/20"
          >
            <div class="flex items-center justify-between gap-2">
              <h2 class="text-sm font-semibold text-neutral-100">Restricciones</h2>
              <span class="text-[10px] uppercase tracking-wider text-neutral-500">
                {{ constraints.length }} {{ constraints.length === 1 ? 'restricción' : 'restricciones' }}
              </span>
            </div>

            <div class="mt-3 space-y-3">
              <div
                v-for="(constraint, index) in constraints"
                :key="index"
                class="rounded-xl border border-neutral-800 bg-neutral-950/60 p-3"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="inline-flex items-center gap-2 text-xs font-medium text-neutral-300">
                    <span class="h-2 w-2 rounded-full bg-indigo-400" />
                    R{{ index + 1 }}
                  </span>
                  <button
                    type="button"
                    class="text-[11px] text-neutral-500 transition hover:text-rose-300 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:text-neutral-500"
                    :disabled="constraints.length === 1"
                    @click="removeConstraint(index)"
                  >
                    Eliminar
                  </button>
                </div>

                <div class="mt-2 flex items-center gap-1.5">
                  <input
                    v-model="constraint.a1"
                    type="number"
                    step="any"
                    placeholder="a₁"
                    class="min-w-0 flex-1"
                    :class="fieldClass"
                  />
                  <span class="text-xs text-neutral-500">x₁</span>
                  <span class="text-xs text-neutral-600">+</span>
                  <input
                    v-model="constraint.a2"
                    type="number"
                    step="any"
                    placeholder="a₂"
                    class="min-w-0 flex-1"
                    :class="fieldClass"
                  />
                  <span class="text-xs text-neutral-500">x₂</span>
                </div>

                <div class="mt-1.5 grid grid-cols-[auto_1fr] gap-1.5">
                  <select v-model="constraint.op" :class="selectClass">
                    <option v-for="option in OP_OPTIONS" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-model="constraint.b"
                    type="number"
                    step="any"
                    placeholder="lado derecho"
                    class="w-full"
                    :class="fieldClass"
                  />
                </div>

                <p class="mt-2 truncate font-mono text-[11px] text-neutral-500">
                  R{{ index + 1 }}: {{ constraintPreviews[index] }}
                </p>
              </div>
            </div>

            <button
              type="button"
              class="mt-3 w-full rounded-lg border border-dashed border-neutral-700 px-3 py-2 text-xs font-medium text-neutral-400 transition hover:border-indigo-500 hover:text-indigo-200"
              @click="addConstraint"
            >
              + Agregar restricción
            </button>

            <p
              class="mt-3 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-2.5 py-2 text-[11px] text-indigo-200"
            >
              No negatividad implícita: <span class="font-mono">x₁ ≥ 0</span> y
              <span class="font-mono">x₂ ≥ 0</span>.
            </p>
          </section>

          <div class="space-y-2">
            <button
              type="submit"
              :disabled="loading"
              class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-950/40 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <svg
                v-if="loading"
                class="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-90"
                  fill="currentColor"
                  d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z"
                />
              </svg>
              {{ loading ? 'Resolviendo…' : 'Resolver y graficar' }}
            </button>

            <div class="grid grid-cols-2 gap-2">
              <button
                type="button"
                class="rounded-lg border border-neutral-700 px-3 py-2 text-xs font-medium text-neutral-300 transition hover:border-neutral-600 hover:text-white"
                @click="loadExample"
              >
                Cargar ejemplo
              </button>
              <button
                type="button"
                class="rounded-lg border border-neutral-700 px-3 py-2 text-xs font-medium text-neutral-300 transition hover:border-neutral-600 hover:text-white"
                @click="clearForm"
              >
                Limpiar
              </button>
            </div>
          </div>

          <p
            v-if="!bridgeReady"
            class="rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-2 text-[11px] leading-relaxed text-amber-100"
          >
            Motor Python no detectado. Ejecuta el módulo con
            <code class="rounded bg-black/30 px-1 py-0.5 font-mono">python -m optilab.graphic_method</code>
            para usar el puente de pywebview.
          </p>

          <p
            v-if="error"
            class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-2.5 py-2 text-[11px] leading-relaxed text-rose-100"
          >
            {{ error }}
          </p>
        </form>
      </aside>

      <section class="space-y-4">
        <div
          v-if="!result"
          class="flex min-h-[460px] items-center justify-center rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-8 text-center"
        >
          <div class="max-w-sm">
            <div
              class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-neutral-800/80 text-neutral-500"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                class="h-7 w-7"
              >
                <path
                  d="M4 19V5M4 19h16M7 15l4-4 3 2 5-6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <h2 class="mt-4 text-base font-semibold text-neutral-200">
              Listo para resolver
            </h2>
            <p class="mt-1 text-sm leading-relaxed text-neutral-500">
              Define la función objetivo y al menos una restricción. Al resolver verás la región
              factible, los cortes con los ejes y todos los puntos de intersección.
            </p>
          </div>
        </div>

        <template v-if="result">
          <div class="rounded-2xl border p-5" :class="statusClasses">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p
                  class="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-400"
                >
                  {{ statusTitle }}
                </p>

                <div
                  v-if="result.status === 'optimal'"
                  class="mt-2 flex flex-wrap items-baseline gap-x-5 gap-y-1"
                >
                  <p class="text-3xl font-semibold tracking-tight text-white">
                    Z = {{ formatNumber(result.optimal.z) }}
                  </p>
                  <p class="font-mono text-sm text-neutral-200">
                    x₁ = {{ formatNumber(result.optimal.x1) }}
                  </p>
                  <p class="font-mono text-sm text-neutral-200">
                    x₂ = {{ formatNumber(result.optimal.x2) }}
                  </p>
                </div>

                <p v-else class="mt-2 max-w-2xl text-sm leading-relaxed text-neutral-200">
                  {{ statusMessage }}
                </p>
              </div>

              <span
                v-if="result.status === 'optimal'"
                class="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-medium text-emerald-200 ring-1 ring-inset ring-emerald-400/30"
              >
                Punto {{ result.optimal.label }}
              </span>
            </div>

            <div
              v-if="result.status === 'optimal'"
              class="mt-3 flex flex-wrap gap-2 text-[11px] text-neutral-300"
            >
              <span class="rounded-md bg-black/20 px-2 py-1">
                Restricciones activas:
                {{ result.optimal.active.join(', ') || '—' }}
              </span>
              <span
                v-if="multipleOptima"
                class="rounded-md bg-emerald-400/10 px-2 py-1 text-emerald-200"
              >
                Múltiples óptimos:
                {{ result.optimal_points.map((point) => point.label).join(', ') }}
              </span>
            </div>
          </div>

          <section
            class="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-lg shadow-black/20"
          >
            <div
              class="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-800 px-4 py-3"
            >
              <div>
                <h2 class="text-sm font-semibold text-neutral-100">Gráfica de la región factible</h2>
                <p class="text-xs text-neutral-500">
                  Pasa el cursor por los puntos para ver su valor de Z.
                </p>
              </div>
              <label
                class="inline-flex cursor-pointer items-center gap-2 text-xs text-neutral-300"
              >
                <input
                  v-model="showObjective"
                  type="checkbox"
                  class="h-3.5 w-3.5 rounded border-neutral-600 bg-neutral-900 accent-indigo-500"
                />
                Recta objetivo
              </label>
            </div>
            <div class="p-2 sm:p-3">
              <FeasibleChart :result="result" :show-objective="showObjective" />
            </div>
            <p class="border-t border-neutral-800 px-4 py-2.5 text-xs text-neutral-500">
              {{ regionNote }}
            </p>
          </section>

          <div class="grid gap-4 xl:grid-cols-2">
            <section
              class="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-lg shadow-black/20"
            >
              <div class="border-b border-neutral-800 px-4 py-3">
                <h2 class="text-sm font-semibold text-neutral-100">Cortes con los ejes</h2>
                <p class="text-xs text-neutral-500">
                  Cómo se obtiene cada corte haciendo x₁ = 0 o x₂ = 0.
                </p>
              </div>
              <div class="max-h-[460px] space-y-3 overflow-y-auto p-4">
                <article
                  v-for="item in result.intercepts"
                  :key="item.label"
                  class="rounded-xl border border-neutral-800 bg-neutral-950/60 p-3"
                >
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <span
                      class="rounded-full bg-indigo-500/15 px-2 py-0.5 text-[10px] font-semibold text-indigo-200 ring-1 ring-inset ring-indigo-500/30"
                    >
                      {{ item.label }}
                    </span>
                    <code class="text-xs text-indigo-200">{{ item.equation }}</code>
                  </div>
                  <div class="mt-2 space-y-2 text-[11px] leading-relaxed">
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-neutral-500">Corte con x₁</span>
                        <span class="font-mono text-neutral-300">
                          {{ formatNumber(item.x_intercept) }}
                        </span>
                      </div>
                      <p class="mt-0.5 font-mono text-neutral-400">{{ item.x_calc }}</p>
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-neutral-500">Corte con x₂</span>
                        <span class="font-mono text-neutral-300">
                          {{ formatNumber(item.y_intercept) }}
                        </span>
                      </div>
                      <p class="mt-0.5 font-mono text-neutral-400">{{ item.y_calc }}</p>
                    </div>
                  </div>
                </article>
              </div>
            </section>

            <section
              class="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-lg shadow-black/20"
            >
              <details open class="group">
                <summary
                  class="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3"
                >
                  <div>
                    <h2 class="text-sm font-semibold text-neutral-100">
                      Procedimiento paso a paso
                    </h2>
                    <p class="text-xs text-neutral-500">
                      Modelo, cortes, intersecciones y evaluación de Z.
                    </p>
                  </div>
                  <span class="text-[11px] text-neutral-500 group-open:hidden">Abrir</span>
                  <span class="hidden text-[11px] text-neutral-500 group-open:inline">Cerrar</span>
                </summary>
                <ol class="max-h-[460px] space-y-2 overflow-y-auto border-t border-neutral-800 p-4">
                  <li
                    v-for="(step, index) in result.steps"
                    :key="`${step.title}-${index}`"
                    class="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3"
                  >
                    <p class="text-[11px] font-semibold text-neutral-200">{{ step.title }}</p>
                    <p
                      class="mt-1 whitespace-pre-line font-mono text-[11px] leading-relaxed text-neutral-400"
                    >
                      {{ step.detail }}
                    </p>
                  </li>
                </ol>
              </details>
            </section>
          </div>

          <section
            class="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-lg shadow-black/20"
          >
            <div class="flex flex-wrap items-end justify-between gap-2 px-4 py-3">
              <div>
                <h2 class="text-sm font-semibold text-neutral-100">
                  Todos los puntos de intersección
                </h2>
                <p class="text-xs text-neutral-500">
                  Se incluyen los cortes del primer cuadrante aunque no sean factibles. El óptimo
                  se resalta en verde.
                </p>
              </div>
              <span
                class="rounded-full bg-neutral-800 px-2.5 py-1 text-[10px] font-medium text-neutral-400"
              >
                {{ result.points.length }} puntos
              </span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full min-w-[780px] text-left text-sm">
                <thead
                  class="bg-neutral-950/80 text-[10px] uppercase tracking-wider text-neutral-500"
                >
                  <tr>
                    <th class="px-4 py-2.5 font-medium">Punto</th>
                    <th class="px-4 py-2.5 font-medium">Intersección</th>
                    <th class="px-4 py-2.5 text-right font-medium">x₁</th>
                    <th class="px-4 py-2.5 text-right font-medium">x₂</th>
                    <th class="px-4 py-2.5 text-right font-medium">Z</th>
                    <th class="px-4 py-2.5 font-medium">Factible</th>
                    <th class="px-4 py-2.5 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-neutral-800/80">
                  <tr
                    v-for="point in result.points"
                    :key="point.label"
                    :class="rowClass(point)"
                  >
                    <td class="px-4 py-2 font-mono text-xs font-semibold">{{ point.label }}</td>
                    <td class="px-4 py-2 text-[11px] text-neutral-400">
                      {{ point.sources.join(' · ') }}
                    </td>
                    <td class="px-4 py-2 text-right font-mono text-xs">
                      {{ formatNumber(point.x1) }}
                    </td>
                    <td class="px-4 py-2 text-right font-mono text-xs">
                      {{ formatNumber(point.x2) }}
                    </td>
                    <td class="px-4 py-2 text-right font-mono text-xs font-medium">
                      {{ formatNumber(point.z) }}
                    </td>
                    <td class="px-4 py-2">
                      <span
                        class="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium"
                        :class="
                          point.feasible
                            ? 'bg-sky-500/15 text-sky-200'
                            : 'bg-neutral-800 text-neutral-500'
                        "
                      >
                        {{ point.feasible ? 'Sí' : 'No' }}
                      </span>
                    </td>
                    <td class="px-4 py-2">
                      <span :class="pointStateClass(point)">{{ pointState(point) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </section>
    </main>
  </div>
</template>
