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
    <table class="w-full border-collapse text-left">
      <thead>
        <tr class="border-b border-neutral-700 text-neutral-300">
          <th class="py-3 pr-5">Solución inicial</th>
          <th class="py-3 pr-5">Costo inicial</th>
          <th class="py-3 pr-5">Iteraciones MODI</th>
          <th class="py-3">Costo final</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(f, k) in filas" :key="k"
          class="border-b border-neutral-800"
          :class="hayMejor && f.iteraciones === menosIteraciones ? 'bg-emerald-950/50 text-emerald-300' : k % 2 ? 'bg-neutral-900/40' : ''"
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
