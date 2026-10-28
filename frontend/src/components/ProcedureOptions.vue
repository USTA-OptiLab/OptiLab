<script setup>
const opciones = defineModel({ required: true })

const CASILLAS = [
  ['mostrar_inicial', 'Solución inicial'],
  ['mostrar_asignacion_por_iteracion', 'Tabla de cada iteración'],
  ['mostrar_potenciales', 'Potenciales u, v'],
  ['mostrar_costos_reducidos', 'Costos reducidos Δ'],
  ['mostrar_ciclo', 'Ciclo, θ y celda que sale'],
]
</script>

<template>
  <div class="space-y-1 text-sm">
    <label class="flex items-center gap-2">
      <input v-model="opciones.mostrar_procedimiento" type="checkbox" />
      Mostrar el procedimiento completo
    </label>
    <p class="pl-5 text-xs text-neutral-500">Sin marcar: solo el resultado final</p>
    <label class="flex items-center gap-2">
      <input v-model="opciones.paso_a_paso" type="checkbox" />
      Pausar paso a paso
    </label>
    <p class="pt-2 text-neutral-400">Incluir en cada paso:</p>
    <label v-for="[attr, texto] in CASILLAS" :key="attr" class="flex items-center gap-2 pl-3">
      <input v-model="opciones[attr]" type="checkbox" />
      {{ texto }}
    </label>
  </div>
</template>
