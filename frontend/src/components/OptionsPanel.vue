<script setup>
const opciones = defineModel({ required: true })

const METODOS = [
  { valor: 'vogel', texto: 'Aproximación de Vogel' },
  { valor: 'costo_minimo', texto: 'Costo mínimo' },
  { valor: 'noroeste', texto: 'Esquina noroeste' },
]
const MODOS = [
  { valor: 'minimizar', texto: 'minimizar' },
  { valor: 'maximizar', texto: 'maximizar' },
]
const CRITERIOS = [
  { valor: 'mas_negativo', texto: 'Δ más negativo' },
  { valor: 'primero_negativo', texto: 'Primer Δ negativo' },
]
</script>

<template>
  <div class="space-y-2 text-sm">
    <label class="flex items-center justify-between gap-2">
      Solución inicial
      <select v-model="opciones.metodo_inicial" class="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5">
        <option v-for="m in METODOS" :key="m.valor" :value="m.valor">{{ m.texto }}</option>
      </select>
    </label>
    <label class="flex items-center justify-between gap-2">
      Objetivo
      <select v-model="opciones.modo" class="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5">
        <option v-for="m in MODOS" :key="m.valor" :value="m.valor">{{ m.texto }}</option>
      </select>
    </label>
    <label class="flex items-center justify-between gap-2">
      Celda entrante
      <select v-model="opciones.criterio_entrada" class="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5">
        <option v-for="c in CRITERIOS" :key="c.valor" :value="c.valor">{{ c.texto }}</option>
      </select>
    </label>
    <label class="flex items-center justify-between gap-2">
      Decimales
      <input v-model.number="opciones.decimales" type="number" min="0" max="8" class="w-16 rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5 text-center" />
    </label>
    <label class="flex items-center justify-between gap-2">
      Máx. iteraciones
      <input v-model.number="opciones.max_iteraciones" type="number" min="1" max="10000" class="w-20 rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5 text-center" />
    </label>
  </div>
</template>
