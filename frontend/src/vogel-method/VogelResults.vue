<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  result: { type: Object, required: true },
})
const selectedStepIndex = ref(0)
watch(() => props.result, () => { selectedStepIndex.value = 0 })

const steps = computed(() => props.result.steps ?? [])
const step = computed(() => steps.value[selectedStepIndex.value] ?? null)
const rowLabels = computed(() => props.result.supply.map((_, i) =>
  props.result.dummy === 'row' && i === props.result.supply.length - 1 ? 'Ficticio' : `O${i + 1}`,
))
const colLabels = computed(() => props.result.demand.map((_, i) =>
  props.result.dummy === 'column' && i === props.result.demand.length - 1 ? 'Ficticio' : `D${i + 1}`,
))
const formatNumber = (value) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 3 }).format(value)
const totalAssigned = computed(() => props.result.allocation.flat().reduce((sum, qty) => sum + qty, 0))
const selectedRowName = computed(() => step.value?.line[0] === 'row'
  ? rowLabels.value[step.value.line[1]] : colLabels.value[step.value.line[1]])
const crossedName = computed(() => step.value?.crossed[0] === 'row'
  ? rowLabels.value[step.value.crossed[1]] : colLabels.value[step.value.crossed[1]])
const cumulative = computed(() => {
  const quantities = props.result.costs.map((row) => row.map(() => 0))
  steps.value.slice(0, selectedStepIndex.value + 1).forEach((current) => {
    quantities[current.cell[0]][current.cell[1]] += current.quantity
  })
  return quantities
})
function changeStep(offset) {
  selectedStepIndex.value = Math.min(steps.value.length - 1, Math.max(0, selectedStepIndex.value + offset))
}
function isSelectedCell(i, j) {
  return step.value && step.value.cell[0] === i && step.value.cell[1] === j
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-400">Solución obtenida</div>
        <h2 class="text-2xl font-bold tracking-tight text-white">Resultados del método</h2>
        <p class="mt-2 text-sm text-slate-400">Explora las asignaciones y las decisiones tomadas en cada iteración.</p>
      </div>
      <span class="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-300">✓ Cálculo completado</span>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-indigo-400/25 bg-gradient-to-br from-indigo-500/20 to-[var(--color-neutral-900)] p-5 sm:p-6">
        <div class="text-xs font-semibold uppercase tracking-[0.12em] text-indigo-200">{{ result.maximize ? 'Ganancia total estimada' : 'Costo total estimado' }}</div>
        <div class="mt-4 text-4xl font-bold tracking-tight tabular-nums text-white">{{ formatNumber(result.total_cost) }}</div>
        <p class="mt-3 text-xs text-indigo-200/70">{{ result.maximize ? 'Beneficio' : 'Costo' }} de la solución inicial</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-[var(--color-neutral-900)] p-5 sm:p-6">
        <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Unidades asignadas</div>
        <div class="mt-4 text-4xl font-bold tracking-tight tabular-nums text-white">{{ formatNumber(totalAssigned) }}</div>
        <p class="mt-3 text-xs text-slate-500">Distribuidas entre los destinos</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-[var(--color-neutral-900)] p-5 sm:p-6">
        <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Iteraciones</div>
        <div class="mt-4 text-4xl font-bold tracking-tight tabular-nums text-white">{{ steps.length }}</div>
        <p class="mt-3 text-xs text-slate-500">Decisiones de asignación registradas</p>
      </div>
    </div>

    <div class="rounded-2xl border border-white/10 bg-[var(--color-neutral-900)] p-5 sm:p-6">
      <div class="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="font-semibold text-white">Matriz de asignación final</h3>
          <p class="mt-1 text-xs text-slate-500">Unidades enviadas de cada origen a cada destino</p>
        </div>
        <span v-if="result.dummy" class="rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1.5 text-xs font-medium text-amber-300">{{ result.dummy === 'row' ? 'Origen ficticio añadido' : 'Destino ficticio añadido' }}</span>
      </div>
      <div class="overflow-x-auto rounded-xl border border-white/10">
        <table class="w-full min-w-max border-separate border-spacing-0 text-center text-sm">
          <thead class="bg-[var(--color-neutral-800)] text-xs text-slate-300">
            <tr>
              <th class="border-r border-b border-white/10 px-4 py-3 text-left">Origen</th>
              <th v-for="(name, j) in colLabels" :key="j" class="min-w-24 border-r border-b border-white/10 px-3 py-3">{{ name }}</th>
              <th class="border-b border-white/10 px-4 py-3 text-indigo-300">Oferta</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in result.allocation" :key="i" class="bg-[var(--color-neutral-900)]">
              <th class="border-r border-b border-white/8 bg-[var(--color-neutral-800)] px-4 py-3 text-left text-xs text-slate-300">{{ rowLabels[i] }}</th>
              <td v-for="(quantity, j) in row" :key="j" class="border-r border-b border-white/8 px-3 py-3 font-semibold tabular-nums" :class="quantity > 0 ? 'bg-emerald-500/5 text-emerald-300' : 'text-slate-600'">{{ formatNumber(quantity) }}</td>
              <td class="border-b border-white/8 px-4 py-3 tabular-nums text-indigo-200">{{ formatNumber(result.supply[i]) }}</td>
            </tr>
            <tr class="bg-[var(--color-neutral-800)]">
              <th class="border-r border-white/10 px-4 py-3 text-left text-xs text-emerald-300">Demanda</th>
              <td v-for="(quantity, j) in result.demand" :key="j" class="border-r border-white/10 px-3 py-3 font-semibold tabular-nums text-emerald-300">{{ formatNumber(quantity) }}</td>
              <td class="px-4 py-3 font-bold tabular-nums text-white">{{ formatNumber(totalAssigned) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="mt-3 text-xs leading-relaxed text-slate-500">El resultado de Vogel es una aproximación inicial: podría mejorarse aplicando un método de optimalidad, como MODI.</p>
    </div>

    <div v-if="step" class="rounded-2xl border border-white/10 bg-[var(--color-neutral-900)] p-5 sm:p-6">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="mb-2 text-xs font-semibold uppercase tracking-[0.15em] text-indigo-300">Proceso detallado</div>
          <h3 class="text-lg font-semibold text-white">Paso {{ selectedStepIndex + 1 }} <span class="font-normal text-slate-500">de {{ steps.length }}</span></h3>
        </div>
        <div class="flex items-center gap-2">
          <button class="rounded-lg border border-white/10 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/5 disabled:opacity-30" aria-label="Paso anterior" :disabled="selectedStepIndex === 0" @click="changeStep(-1)">←</button>
          <button class="rounded-lg border border-white/10 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/5 disabled:opacity-30" aria-label="Paso siguiente" :disabled="selectedStepIndex === steps.length - 1" @click="changeStep(1)">→</button>
        </div>
      </div>

      <div class="mb-6 flex flex-wrap gap-2">
        <button v-for="(_, index) in steps" :key="index" class="h-9 min-w-9 rounded-lg border px-3 text-xs font-bold transition" :class="index === selectedStepIndex ? 'border-indigo-400 bg-indigo-500 text-white' : 'border-white/10 bg-white/5 text-slate-400 hover:border-indigo-400/40'" :aria-label="`Mostrar paso ${index + 1}`" :aria-current="index === selectedStepIndex ? 'step' : undefined" @click="selectedStepIndex = index">{{ index + 1 }}</button>
      </div>

      <div class="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div class="min-w-0">
          <p class="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">{{ step.phase === 'direct' ? 'Asignación directa' : 'Costos y penalizaciones' }} · Paso {{ selectedStepIndex + 1 }}</p>
          <div class="overflow-x-auto rounded-xl border border-white/10">
            <table class="w-full min-w-max border-separate border-spacing-0 text-center text-xs">
              <thead class="bg-[var(--color-neutral-800)] text-slate-300">
                <tr>
                  <th class="border-r border-b border-white/10 px-3 py-3 text-left">Origen</th>
                  <th v-for="(name, j) in colLabels" :key="j" class="min-w-21 border-r border-b border-white/10 px-3 py-3" :class="!step.active_cols.includes(j) ? 'opacity-35' : ''">{{ name }}</th>
                  <th class="border-r border-b border-white/10 px-3 py-3">Oferta</th>
                  <th class="border-b border-white/10 px-3 py-3 text-amber-300">Penal.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in result.costs" :key="i" class="bg-[var(--color-neutral-900)]" :class="!step.active_rows.includes(i) ? 'opacity-40' : ''">
                  <th class="border-r border-b border-white/8 bg-[var(--color-neutral-800)] px-3 py-3 text-left text-slate-300">{{ rowLabels[i] }}</th>
                  <td v-for="(cost, j) in row" :key="j" class="border-r border-b border-white/8 px-3 py-2 tabular-nums" :class="isSelectedCell(i,j) ? 'bg-indigo-500/30 text-white ring-1 ring-inset ring-indigo-400' : !step.active_rows.includes(i) || !step.active_cols.includes(j) ? 'text-slate-600' : 'text-slate-300'">
                    <div class="font-semibold">{{ formatNumber(cost) }}</div>
                    <div v-if="cumulative[i][j] > 0 || isSelectedCell(i,j)" class="mt-1 text-[10px] text-emerald-300">x = {{ formatNumber(cumulative[i][j]) }}</div>
                  </td>
                  <td class="border-r border-b border-white/8 px-3 py-3 text-indigo-200">{{ formatNumber(step.supply_before[i]) }}</td>
                  <td class="border-b border-white/8 px-3 py-3 font-bold text-amber-300">{{ step.row_penalties[i] === undefined ? '—' : formatNumber(step.row_penalties[i]) }}</td>
                </tr>
                <tr class="bg-[var(--color-neutral-800)]">
                  <th class="border-r border-b border-white/10 px-3 py-3 text-left text-emerald-300">Demanda</th>
                  <td v-for="(_, j) in colLabels" :key="j" class="border-r border-b border-white/10 px-3 py-3 font-semibold text-emerald-300">{{ formatNumber(step.demand_before[j]) }}</td>
                  <td class="border-r border-b border-white/10 px-3 py-3 text-slate-500">—</td>
                  <td class="border-b border-white/10 px-3 py-3 text-slate-500">—</td>
                </tr>
                <tr class="bg-[var(--color-neutral-800)]">
                  <th class="border-r border-white/10 px-3 py-3 text-left text-amber-300">Penal.</th>
                  <td v-for="(_, j) in colLabels" :key="j" class="border-r border-white/10 px-3 py-3 font-bold text-amber-300">{{ step.col_penalties[j] === undefined ? '—' : formatNumber(step.col_penalties[j]) }}</td>
                  <td class="border-r border-white/10 px-3 py-3 text-slate-500">—</td>
                  <td class="px-3 py-3 text-slate-500">—</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="mt-3 text-xs text-slate-500">Las filas y columnas atenuadas ya se retiraron. La celda resaltada corresponde a la asignación actual.</p>
        </div>

        <div class="rounded-xl border border-indigo-400/15 bg-[var(--color-neutral-900)] p-5">
          <div class="mb-5 text-xs font-bold uppercase tracking-[0.14em] text-indigo-300">Decisión del algoritmo</div>
          <div class="space-y-5">
            <div>
              <p class="text-xs text-slate-400">{{ step.phase === 'direct' ? 'Etapa final' : 'Mayor penalización' }}</p>
              <p class="mt-1 text-2xl font-bold tabular-nums text-white">{{ step.phase === 'direct' ? 'Asignación directa' : formatNumber(step.max_penalty) }}</p>
              <p class="mt-1 text-xs text-slate-400">{{ step.line[0] === 'row' ? 'Fila' : 'Columna' }} {{ selectedRowName }}</p>
            </div>
            <p v-if="step.phase === 'direct'" class="text-xs leading-relaxed text-slate-400">Solo queda una fila o columna. Se asigna lo restante sin calcular penalizaciones.</p>
            <div class="h-px bg-white/10"></div>
            <div>
              <p class="text-xs text-slate-400">Celda seleccionada</p>
              <p class="mt-1 font-semibold text-white">{{ rowLabels[step.cell[0]] }} → {{ colLabels[step.cell[1]] }}</p>
              <p class="mt-1 text-xs text-slate-400">Valor unitario: {{ formatNumber(result.costs[step.cell[0]][step.cell[1]]) }}</p>
            </div>
            <div class="rounded-lg border border-emerald-500/20 bg-emerald-500/8 p-3">
              <p class="text-xs font-medium text-emerald-300">Cantidad asignada</p>
              <p class="mt-1 text-2xl font-bold tabular-nums text-white">{{ formatNumber(step.quantity) }}</p>
              <p class="mt-1 text-xs text-emerald-200/70">Mínimo entre oferta y demanda</p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Se retira {{ step.crossed[0] === 'row' ? 'la fila' : 'la columna' }}</p>
              <p class="mt-1 text-sm font-semibold text-white">{{ crossedName }}</p>
            </div>
            <p v-if="step.tied_lines > 1" class="rounded-lg border border-amber-400/15 bg-amber-400/5 p-3 text-xs leading-relaxed text-amber-200">Hubo {{ step.tied_lines }} líneas con igual penalización. Se desempató por mejor valor unitario y mayor cantidad asignable; si persiste el empate, se conserva el orden de filas y columnas.</p>
          </div>
        </div>
      </div>
    </div>
    <div v-if="result.interpretation" class="rounded-2xl border border-white/10 bg-[var(--color-neutral-900)] p-5 sm:p-6">
      <div class="mb-2 text-xs font-semibold uppercase tracking-[0.15em] text-indigo-300">Lectura de la solución</div>
      <h3 class="text-lg font-semibold text-white">Interpretación del problema</h3>
      <div class="mt-5 rounded-xl border border-indigo-400/15 bg-[var(--color-neutral-900)] p-4">
        <p class="text-xs font-semibold text-indigo-300">Contexto del problema</p>
        <p class="mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-300">{{ result.context }}</p>
      </div>
      <p class="mt-5 text-sm leading-relaxed text-slate-300">Con {{ result.interpretation.origins }} orígenes y {{ result.interpretation.destinations }} destinos, la distribución inicial encontrada es:</p>
      <ul v-if="result.interpretation.shipments.length" class="mt-4 grid gap-2 sm:grid-cols-2">
        <li v-for="shipment in result.interpretation.shipments" :key="shipment.origin + '-' + shipment.destination" class="rounded-lg border border-white/8 bg-[var(--color-neutral-900)] px-4 py-3 text-sm leading-relaxed text-slate-300">
          El origen <span class="font-semibold text-indigo-300">O{{ shipment.origin }}</span> envía <span class="font-semibold text-emerald-300">{{ formatNumber(shipment.quantity) }} unidades</span> al destino <span class="font-semibold text-indigo-300">D{{ shipment.destination }}</span>.
        </li>
      </ul>
      <p v-else class="mt-4 text-sm text-slate-400">No hay envíos entre los orígenes y destinos reales.</p>
      <p v-if="result.interpretation.surplus > 0" class="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/5 p-4 text-sm leading-relaxed text-amber-200">Sobra oferta: {{ formatNumber(result.interpretation.surplus) }} unidades quedan sin enviar y se asignan al destino ficticio.</p>
      <p v-if="result.interpretation.unmet > 0" class="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/5 p-4 text-sm leading-relaxed text-amber-200">Falta oferta: {{ formatNumber(result.interpretation.unmet) }} unidades de demanda no se cubren. El origen ficticio representa este faltante, no un envío real.</p>
      <p class="mt-5 text-sm leading-relaxed text-slate-300">{{ result.maximize ? 'La ganancia total' : 'El costo total de transporte' }} de esta solución inicial es <span class="font-bold text-white">{{ formatNumber(result.total_cost) }}</span>.</p>
      <p class="mt-3 text-xs leading-relaxed text-slate-500">Es una solución inicial factible del modelo de transporte balanceado; no necesariamente es la óptima.</p>
    </div>
  </div>
</template>
