<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })

const reasons = {
  infeasible: 'Infactible',
  unbounded: 'No acotado',
}

const dualOk = computed(() => props.data.result.status === 'optimal')
const primalOk = computed(() => props.data.primal_result?.status === 'optimal')
const strong = computed(
  () => dualOk.value && primalOk.value && props.data.result.z.frac === props.data.primal_result.z.frac,
)

const card = 'rounded-xl border border-slate-800 bg-slate-900/50 p-5'
const title = 'mb-3 text-sm font-medium uppercase tracking-wide text-slate-400'
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-5 md:grid-cols-2">
      <section v-for="(box, key) in { Primal: data.primal, 'Dual (construido)': data.dual }" :key="key" :class="card">
        <h3 :class="title">{{ key }}</h3>
        <p class="font-mono text-sm text-sky-300">{{ box.objective }}</p>
        <p class="mt-2 text-xs text-slate-500">sujeto a</p>
        <p v-for="(c, i) in box.constraints" :key="i" class="font-mono text-sm">{{ c }}</p>
        <p class="mt-2 font-mono text-sm text-slate-400">{{ box.signs.join(' · ') }}</p>
      </section>
    </div>

    <section :class="card">
      <h3 :class="title">Solución del dual</h3>
      <template v-if="dualOk">
        <p class="text-sm text-slate-400">{{ data.result.method }}</p>
        <p class="mt-1 text-2xl font-semibold text-emerald-400">
          Z = {{ data.result.z.frac }}
          <span v-if="data.result.z.frac.includes('/')" class="text-sm font-normal text-slate-400">
            ≈ {{ +data.result.z.value.toPrecision(6) }}
          </span>
        </p>
        <table class="mt-3 text-sm">
          <tr v-for="v in data.result.vars" :key="v.name">
            <td class="pr-4 font-mono text-slate-400">{{ v.name }}</td>
            <td class="font-mono">
              {{ v.frac }}
              <span v-if="v.frac.includes('/')" class="text-slate-500">≈ {{ +v.value.toPrecision(6) }}</span>
            </td>
          </tr>
        </table>
      </template>
      <template v-else>
        <p class="text-lg font-semibold text-amber-400">No es óptima</p>
        <p class="text-sm text-slate-400">Dual: {{ reasons[data.result.status] ?? data.result.status }}</p>
      </template>
    </section>

    <section v-if="data.primal_result" :class="card">
      <h3 :class="title">Verificación con el primal</h3>
      <template v-if="primalOk">
        <p class="font-mono text-sm">
          Z = {{ data.primal_result.z.frac }}
          <span class="text-slate-400">
            ·
            <template v-for="(v, i) in data.primal_result.vars" :key="v.name">
              {{ v.name }} = {{ v.frac }}{{ i < data.primal_result.vars.length - 1 ? ' · ' : '' }}
            </template>
          </span>
        </p>
        <p v-if="strong" class="mt-2 text-sm text-emerald-400">✓ Dualidad fuerte: Z primal = Z dual</p>
      </template>
      <template v-else>
        <p class="text-sm text-amber-400">
          No es óptima ({{ reasons[data.primal_result.status] ?? data.primal_result.status }})
        </p>
      </template>
    </section>
  </div>
</template>
