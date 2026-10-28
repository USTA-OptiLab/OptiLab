<script setup>
defineProps({
  step: { type: Object, required: true },
})
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full border-collapse font-mono text-sm">
      <thead>
        <tr class="text-neutral-400">
          <th class="border border-neutral-800 px-3 py-1.5 text-left">VB</th>
          <th
            v-for="(col, j) in step.columns"
            :key="col"
            class="border border-neutral-800 px-3 py-1.5"
            :class="step.pivot?.col === j ? 'bg-indigo-950 text-indigo-200' : ''"
          >
            {{ col }}
          </th>
          <th class="border border-neutral-800 px-3 py-1.5">K</th>
        </tr>
      </thead>
      <tbody>
        <tr class="bg-neutral-900 font-semibold text-amber-300">
          <td class="border border-neutral-800 px-3 py-1.5">{{ step.objective.label }}</td>
          <td
            v-for="(v, j) in step.objective.values"
            :key="j"
            class="border border-neutral-800 px-3 py-1.5 text-right"
          >
            {{ v }}
          </td>
        </tr>
        <tr v-for="(row, i) in step.rows" :key="i">
          <td class="border border-neutral-800 px-3 py-1.5 font-semibold text-indigo-300">{{ row.basis }}</td>
          <td
            v-for="(v, j) in row.values"
            :key="j"
            class="border border-neutral-800 px-3 py-1.5 text-right"
            :class="
              step.pivot?.row === i && step.pivot?.col === j
                ? 'bg-indigo-600 font-bold text-white'
                : step.pivot?.row === i || step.pivot?.col === j
                  ? 'bg-indigo-950/60'
                  : ''
            "
          >
            {{ v }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
