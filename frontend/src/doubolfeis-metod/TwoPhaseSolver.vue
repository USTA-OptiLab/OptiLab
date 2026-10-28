<script setup>
import { computed, ref } from 'vue'
import TableauTable from './TableauTable.vue'

const SUB = '₀₁₂₃₄₅₆₇₈₉'
const sub = (n) => String(n).replace(/\d/g, (d) => SUB[d])

// Ejemplo del curso: MAX Z = 5x₁ + 8x₂
const sense = ref('max')
const objective = ref(['5', '8'])
const constraints = ref([
  { coefs: ['2', '1'], type: '=', rhs: '12' },
  { coefs: ['1', '1'], type: '>=', rhs: '8' },
  { coefs: ['0', '1'], type: '<=', rhs: '8' },
])

const result = ref(null)
const error = ref('')
const loading = ref(false)

const numVars = computed(() => objective.value.length)

function addVariable() {
  objective.value.push('0')
  constraints.value.forEach((c) => c.coefs.push('0'))
}

function removeVariable() {
  if (numVars.value <= 1) return
  objective.value.pop()
  constraints.value.forEach((c) => c.coefs.pop())
}

function addConstraint() {
  constraints.value.push({ coefs: Array(numVars.value).fill('0'), type: '<=', rhs: '0' })
}

function removeConstraint(i) {
  if (constraints.value.length > 1) constraints.value.splice(i, 1)
}

function bridge() {
  if (window.pywebview?.api) return Promise.resolve(window.pywebview.api)
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('El backend de Python (pywebview) no está disponible.')), 3000)
    window.addEventListener('pywebviewready', () => {
      clearTimeout(timer)
      resolve(window.pywebview.api)
    }, { once: true })
  })
}

async function solve() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const api = await bridge()
    const res = await api.two_phase({
      sense: sense.value,
      objective: objective.value,
      constraints: constraints.value,
    })
    if (res.status === 'error') error.value = res.message
    else result.value = res
  } catch (e) {
    error.value = e.message ?? String(e)
  } finally {
    loading.value = false
  }
}

const statusText = {
  optimal: 'Solución óptima',
  infeasible: 'Problema infactible (r > 0 al terminar la Fase 1)',
  unbounded: 'Problema no acotado',
}

const typeLabel = { '<=': '≤', '>=': '≥', '=': '=' }
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-8 p-6">
    <header>
      <h2 class="text-2xl font-semibold">Método de las Dos Fases</h2>
      <p class="text-neutral-400">Fase 1 encuentra factibilidad · Fase 2 encuentra optimalidad</p>
    </header>

    <!-- Modelo -->
    <section class="flex flex-col gap-4 rounded-lg border border-neutral-800 p-4">
      <div class="flex flex-wrap items-center gap-2">
        <select v-model="sense" class="rounded-md bg-neutral-900 px-2 py-1">
          <option value="max">Maximizar</option>
          <option value="min">Minimizar</option>
        </select>
        <span>Z =</span>
        <template v-for="(_, j) in objective" :key="j">
          <span v-if="j > 0">+</span>
          <input v-model="objective[j]" class="w-16 rounded-md bg-neutral-900 px-2 py-1 text-right" />
          <span>x{{ sub(j + 1) }}</span>
        </template>
      </div>

      <div v-for="(con, i) in constraints" :key="i" class="flex flex-wrap items-center gap-2">
        <span class="w-8 text-neutral-400">R{{ sub(i + 1) }}</span>
        <template v-for="(_, j) in con.coefs" :key="j">
          <span v-if="j > 0">+</span>
          <input v-model="con.coefs[j]" class="w-16 rounded-md bg-neutral-900 px-2 py-1 text-right" />
          <span>x{{ sub(j + 1) }}</span>
        </template>
        <select v-model="con.type" class="rounded-md bg-neutral-900 px-2 py-1">
          <option v-for="(label, value) in typeLabel" :key="value" :value="value">{{ label }}</option>
        </select>
        <input v-model="con.rhs" class="w-16 rounded-md bg-neutral-900 px-2 py-1 text-right" />
        <button class="text-neutral-500 hover:text-red-400" title="Quitar restricción" @click="removeConstraint(i)">✕</button>
      </div>

      <p class="text-sm text-neutral-500">
        {{ objective.map((_, j) => `x${sub(j + 1)}`).join(', ') }} ≥ 0 · Se aceptan fracciones como 1/2
      </p>

      <div class="flex flex-wrap gap-2">
        <button class="rounded-md bg-neutral-800 px-3 py-1.5 hover:bg-neutral-700" @click="addVariable">+ Variable</button>
        <button class="rounded-md bg-neutral-800 px-3 py-1.5 hover:bg-neutral-700" @click="removeVariable">− Variable</button>
        <button class="rounded-md bg-neutral-800 px-3 py-1.5 hover:bg-neutral-700" @click="addConstraint">+ Restricción</button>
        <button
          class="ml-auto rounded-md bg-indigo-600 px-4 py-1.5 font-medium hover:bg-indigo-500 disabled:opacity-50"
          :disabled="loading"
          @click="solve"
        >
          {{ loading ? 'Resolviendo…' : 'Resolver' }}
        </button>
      </div>
    </section>

    <p v-if="error" class="rounded-md border border-red-900 bg-red-950/50 p-3 text-red-300">{{ error }}</p>

    <template v-if="result">
      <!-- Resultado -->
      <section
        class="rounded-lg border p-4"
        :class="result.status === 'optimal' ? 'border-emerald-800 bg-emerald-950/30' : 'border-amber-800 bg-amber-950/30'"
      >
        <h3 class="mb-2 text-lg font-semibold">{{ statusText[result.status] }}</h3>
        <div v-if="result.status === 'optimal'" class="flex flex-wrap gap-x-6 gap-y-1 font-mono">
          <span v-for="(v, name) in result.solution" :key="name">{{ name }} = {{ v }}</span>
          <span class="font-bold text-emerald-300">
            Z{{ sense === 'max' ? 'max' : 'min' }} = {{ result.z }}
            <template v-if="result.z.includes('/')"> ≈ {{ result.z_float.toFixed(4) }}</template>
          </span>
        </div>
      </section>

      <!-- Procedimiento -->
      <section
        v-for="(step, k) in result.steps"
        :key="k"
        class="flex flex-col gap-3 rounded-lg border p-4"
        :class="step.phase === 1 ? 'border-sky-900' : 'border-violet-900'"
      >
        <div class="flex items-center gap-3">
          <span
            class="rounded px-2 py-0.5 text-xs font-bold"
            :class="step.phase === 1 ? 'bg-sky-900 text-sky-200' : 'bg-violet-900 text-violet-200'"
          >
            FASE {{ step.phase }}
          </span>
          <h3 class="font-semibold">{{ step.title }}</h3>
        </div>

        <ul v-if="step.notes.length" class="list-inside list-disc text-neutral-300">
          <li v-for="(note, n) in step.notes" :key="n">{{ note }}</li>
        </ul>

        <div v-if="step.ratios" class="text-sm">
          <p class="mb-1 text-neutral-400">Razón mínima (K / aᵢⱼ, sólo aᵢⱼ &gt; 0):</p>
          <ul class="font-mono">
            <li
              v-for="(r, n) in step.ratios"
              :key="n"
              :class="r.basis === step.leaving ? 'text-amber-300' : r.ratio === null ? 'text-neutral-500' : ''"
            >
              {{ r.basis }}: {{ r.text }}
            </li>
          </ul>
        </div>

        <div v-if="step.operations.length" class="text-sm">
          <p class="mb-1 text-neutral-400">Operaciones:</p>
          <ul class="font-mono text-neutral-300">
            <li v-for="(op, n) in step.operations" :key="n">{{ op }}</li>
          </ul>
        </div>

        <TableauTable v-if="step.columns" :step="step" />
      </section>
    </template>
  </div>
</template>
