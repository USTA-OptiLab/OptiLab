<script setup>
import { computed } from 'vue'

const opciones = defineModel({ required: true })

const CASILLAS = [
  ['mostrar_inicial', 'Solución inicial'],
  ['mostrar_asignacion_por_iteracion', 'Tabla de cada iteración'],
  ['mostrar_potenciales', 'Potenciales u, v'],
  ['mostrar_costos_reducidos', 'Costos reducidos Δ'],
  ['mostrar_ciclo', 'Ciclo, θ y celda que sale'],
]

// Un solo interruptor: "paso a paso" también decide si se muestra el procedimiento
// completo o solo el resultado final, en vez de dos opciones independientes.
const pasoAPaso = computed({
  get: () => opciones.value.paso_a_paso,
  set: (valor) => {
    opciones.value.paso_a_paso = valor
    opciones.value.mostrar_procedimiento = valor
  },
})
</script>

<template>
  <div class="space-y-1 text-sm">
    <label class="flex items-center gap-2">
      <input v-model="pasoAPaso" type="checkbox" class="h-3.5 w-3.5 rounded border-neutral-600 bg-neutral-900 accent-indigo-500" />
      Mostrar paso a paso
    </label>
    <p class="pl-5 text-xs text-neutral-500">Sin marcar: solo el resultado final</p>
    <p class="pt-2 text-neutral-400">Incluir en cada paso:</p>
    <label
      v-for="[attr, texto] in CASILLAS" :key="attr"
      class="flex items-center gap-2 pl-3"
      :class="{ 'opacity-40': !pasoAPaso }"
    >
      <input
        v-model="opciones[attr]" type="checkbox" :disabled="!pasoAPaso"
        class="h-3.5 w-3.5 rounded border-neutral-600 bg-neutral-900 accent-indigo-500"
      />
      {{ texto }}
    </label>
  </div>
</template>
