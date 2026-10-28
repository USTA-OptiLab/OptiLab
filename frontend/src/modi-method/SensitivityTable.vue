<script setup>
defineProps({
  filas: { type: Array, default: () => [] },
  decimales: { type: Number, default: 2 },
  error: { type: String, default: '' },
})

function num(x, dec) {
  if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x))
  return Number(x).toFixed(dec)
}
</script>

<template>
  <div class="space-y-2 text-base">
    <p class="text-neutral-400">
      Rango en el que puede variar el costo de cada ruta (los demás fijos) sin cambiar la solución óptima.
    </p>
    <p v-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-2.5 py-2 text-sm text-rose-100">{{ error }}</p>
    <table v-else class="w-full text-left">
      <thead class="text-[11px] uppercase tracking-wider text-neutral-500">
        <tr>
          <th class="py-3 pr-5 font-medium">Ruta</th>
          <th class="py-3 pr-5 font-medium">Tipo</th>
          <th class="py-3 pr-5 font-medium">Costo</th>
          <th class="py-3 font-medium">Rango del costo</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-neutral-800/80">
        <tr
          v-for="(f, k) in filas" :key="k"
          :class="f.basica ? 'bg-indigo-500/10 text-indigo-100' : k % 2 ? 'bg-neutral-900/40' : ''"
        >
          <td class="py-3 pr-5">{{ f.origen }} → {{ f.destino }}</td>
          <td class="py-3 pr-5">{{ f.basica ? 'básica' : 'no básica' }}</td>
          <td class="py-3 pr-5">{{ num(f.costo, decimales) }}</td>
          <td class="py-3">
            [{{ f.minimo === null ? '-∞' : num(f.minimo, decimales) }}, {{ f.maximo === null ? '+∞' : num(f.maximo, decimales) }}]
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
