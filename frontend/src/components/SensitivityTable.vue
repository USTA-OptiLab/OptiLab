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
  <div class="space-y-2 text-sm">
    <p class="text-neutral-400">
      Rango en el que puede variar el costo de cada ruta (los demás fijos) sin cambiar la solución óptima.
    </p>
    <p v-if="error" class="text-rose-400">{{ error }}</p>
    <table v-else class="w-full border-collapse text-left">
      <thead>
        <tr class="border-b border-neutral-700 text-neutral-300">
          <th class="py-2 pr-4">Ruta</th>
          <th class="py-2 pr-4">Tipo</th>
          <th class="py-2 pr-4">Costo</th>
          <th class="py-2">Rango del costo</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(f, k) in filas" :key="k"
          class="border-b border-neutral-800"
          :class="f.basica ? 'bg-indigo-950/40' : k % 2 ? 'bg-neutral-900/40' : ''"
        >
          <td class="py-2 pr-4">{{ f.origen }} → {{ f.destino }}</td>
          <td class="py-2 pr-4">{{ f.basica ? 'básica' : 'no básica' }}</td>
          <td class="py-2 pr-4">{{ num(f.costo, decimales) }}</td>
          <td class="py-2">
            [{{ f.minimo === null ? '-∞' : num(f.minimo, decimales) }}, {{ f.maximo === null ? '+∞' : num(f.maximo, decimales) }}]
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
