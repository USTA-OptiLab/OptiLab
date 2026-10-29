<script setup>
import { onMounted, reactive, ref } from 'vue'
import ProblemForm from './ProblemForm.vue'
import ResultPanel from './ResultPanel.vue'
import { examples } from './examples.js'

const clone = (x) => JSON.parse(JSON.stringify(x))

const form = reactive(clone(examples[0].p))
const verify = ref(true)
const loading = ref(false)
const error = ref('')
const data = ref(null)
const example = ref('')

function loadExample() {
  const ex = examples.find((e) => e.name === example.value)
  if (!ex) return
  Object.assign(form, clone(ex.p))
  data.value = null
  error.value = ''
}

async function solve() {
  error.value = ''
  const api = window.pywebview?.api
  if (!api) {
    error.value = 'Sin conexión con Python: ejecuta la app con `just dev` o `just run`.'
    return
  }
  loading.value = true
  try {
    // structuredClone rompe el puente pywebview en WebKitGTK: usar JSON.
    const res = await api.solve_primal_dual({ ...clone(form), verify: verify.value })
    if (res.status === 'error') {
      error.value = res.message
      data.value = null
    } else {
      data.value = res
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('pywebviewready', () => (error.value = ''))
})
</script>

<template>
  <div class="space-y-5">
    <div>
      <h2 class="text-lg font-semibold">Primal → Dual</h2>
      <p class="text-sm text-slate-400">Ingresa el problema primal; se construye el dual y se resuelve.</p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <select
        v-model="example"
        class="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm outline-none focus:border-sky-500"
        @change="loadExample"
      >
        <option value="" disabled>Cargar ejemplo…</option>
        <option v-for="e in examples" :key="e.name" :value="e.name">{{ e.name }}</option>
      </select>
    </div>

    <ProblemForm :form="form" />

    <div class="flex flex-wrap items-center gap-4">
      <button
        class="rounded-md bg-sky-600 px-5 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
        :disabled="loading"
        @click="solve"
      >
        {{ loading ? 'Resolviendo…' : 'Resolver' }}
      </button>
      <label class="flex items-center gap-2 text-sm text-slate-300">
        <input v-model="verify" type="checkbox" class="accent-sky-500" />
        Verificar resolviendo también el primal
      </label>
    </div>

    <p v-if="error" class="rounded-md border border-red-900 bg-red-950/50 px-4 py-3 text-sm text-red-300">
      {{ error }}
    </p>

    <ResultPanel v-if="data" :data="data" />
  </div>
</template>
