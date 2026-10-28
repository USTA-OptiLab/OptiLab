<script setup>
import { computed } from 'vue'

const props = defineProps({
  filas: { type: Array, default: () => [] },
  decimales: { type: Number, default: 2 },
})

const NOMBRES = { noroeste: 'Esquina noroeste', costo_minimo: 'Costo mínimo', vogel: 'Aproximación de Vogel' }

function num(x, dec) {
  if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x))
  return Number(x).toFixed(dec)
}

const menosIteraciones = computed(() => Math.min(...props.filas.map((f) => f.iteraciones)))
const hayMejor = computed(() => props.filas.some((f) => f.iteraciones !== menosIteraciones.value))
</script>

<template>
  <div class="space-y-2 text-base">
    <p class="text-neutral-400">
      Mismo problema resuelto con cada solución inicial. En verde, la que necesitó menos iteraciones de MODI.
    </p>
    <table class="w-full text-left">
      <thead class="text-[11px] uppercase tracking-wider text-neutral-500">
        <tr>
          <th class="py-3 pr-5 font-medium">Solución inicial</th>
          <th class="py-3 pr-5 font-medium">Costo inicial</th>
          <th class="py-3 pr-5 font-medium">Iteraciones MODI</th>
          <th class="py-3 font-medium">Costo final</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-neutral-800/80">
        <tr
          v-for="(f, k) in filas" :key="k"
          :class="hayMejor && f.iteraciones === menosIteraciones ? 'bg-emerald-500/10 text-emerald-200' : k % 2 ? 'bg-neutral-900/40' : ''"
        >
          <td class="py-3 pr-5">{{ NOMBRES[f.metodo] }}</td>
          <td class="py-3 pr-5">{{ num(f.costo_inicial, decimales) }}</td>
          <td class="py-3 pr-5">{{ f.iteraciones }}</td>
          <td class="py-3">{{ num(f.costo_final, decimales) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
