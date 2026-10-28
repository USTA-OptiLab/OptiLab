<script setup>
import { shallowRef } from 'vue'
import GraphicMethod from './graphic-method/GraphicMethod.vue'

// Cada método nuevo se agrega aquí para que aparezca en el menú
const methods = [
  {
    id: 'graphic',
    name: 'Método Gráfico',
    description: 'Programación lineal con dos variables: región factible, vértices y solución óptima.',
    component: GraphicMethod,
  },
]

const current = shallowRef(null)
</script>

<template>
  <div class="min-h-screen bg-neutral-950 text-neutral-100">
    <header class="flex items-center gap-4 border-b border-neutral-800 px-6 py-4">
      <h1 class="text-2xl font-semibold">OptiLab</h1>
      <button
        v-if="current"
        class="rounded-md bg-neutral-800 px-3 py-1.5 text-sm hover:bg-neutral-700"
        @click="current = null"
      >
        ← Menú
      </button>
    </header>

    <component :is="current.component" v-if="current" />

    <main v-else class="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <div>
        <h2 class="text-xl font-semibold">Métodos</h2>
        <p class="text-neutral-400">Elige un método para resolver</p>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <button
          v-for="method in methods"
          :key="method.id"
          class="group flex flex-col gap-2 rounded-lg border border-neutral-800 bg-neutral-900 p-5 text-left transition hover:border-indigo-500 hover:bg-neutral-800"
          @click="current = method"
        >
          <span class="text-lg font-semibold group-hover:text-indigo-300">
            {{ method.name }}
          </span>
          <span class="text-sm text-neutral-400">{{ method.description }}</span>
        </button>
      </div>
    </main>
  </div>
</template>
