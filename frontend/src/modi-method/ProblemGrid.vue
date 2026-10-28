<script setup>
import { nextTick } from 'vue'

const problema = defineModel({ required: true })
const emit = defineEmits(['change'])

const fieldClass =
  'w-16 rounded-md border border-neutral-700 bg-neutral-950 px-1 text-center text-sm text-neutral-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20'
const headerFieldClass = `${fieldClass} py-0.5 font-semibold`
const cellFieldClass = `${fieldClass} py-1`

function redimensionar(m, n) {
  m = Math.max(1, Math.min(12, m))
  n = Math.max(1, Math.min(12, n))
  const p = problema.value
  const origenes = Array.from({ length: m }, (_, i) => p.origenes[i] ?? `O${i + 1}`)
  const destinos = Array.from({ length: n }, (_, j) => p.destinos[j] ?? `D${j + 1}`)
  const oferta = Array.from({ length: m }, (_, i) => p.oferta[i] ?? 0)
  const demanda = Array.from({ length: n }, (_, j) => p.demanda[j] ?? 0)
  const costos = Array.from({ length: m }, (_, i) => Array.from({ length: n }, (_, j) => p.costos[i]?.[j] ?? 0))
  problema.value = { m, n, origenes, destinos, oferta, demanda, costos }
  emit('change')
}

function refClave(clave) {
  return `celda-${clave}`
}

const celdas = {}
function registrarCelda(clave, el) {
  if (el) celdas[clave] = el
  else delete celdas[clave]
}

function mover(claveActual, delta, evento) {
  if (evento.ctrlKey || evento.metaKey) return
  evento.preventDefault()
  const [tipo, ...resto] = claveActual.split('-')
  if (tipo !== 'c') return
  const [i, j] = resto.map(Number)
  const siguiente = i + delta
  if (siguiente < 0 || siguiente >= problema.value.m) return
  nextTick(() => celdas[refClave(`c-${siguiente}-${j}`)]?.focus())
}

function limpiar() {
  const p = problema.value
  p.costos = p.costos.map((fila) => fila.map(() => 0))
  p.oferta = p.oferta.map(() => 0)
  p.demanda = p.demanda.map(() => 0)
  emit('change')
}

defineExpose({ limpiar })
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
      <label class="flex items-center gap-1">
        Orígenes
        <input
          type="number" min="1" max="12" :value="problema.m"
          class="w-14 rounded-md border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-center text-sm text-neutral-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
          @change="redimensionar(Number($event.target.value), problema.n)"
        />
      </label>
      <label class="flex items-center gap-1">
        Destinos
        <input
          type="number" min="1" max="12" :value="problema.n"
          class="w-14 rounded-md border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-center text-sm text-neutral-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
          @change="redimensionar(problema.m, Number($event.target.value))"
        />
      </label>
      <button
        type="button"
        class="ml-auto rounded-lg border border-neutral-700 px-2.5 py-1 text-xs font-medium text-neutral-300 transition hover:border-neutral-600 hover:text-white"
        @click="limpiar"
      >
        Limpiar
      </button>
    </div>

    <div class="overflow-x-auto">
      <table class="border-collapse text-xs">
        <thead>
          <tr>
            <th class="w-16"></th>
            <th v-for="(_destino, j) in problema.destinos" :key="`hd-${j}`" class="px-1 pb-1">
              <input
                :value="problema.destinos[j]"
                :class="headerFieldClass"
                @change="problema.destinos[j] = $event.target.value; emit('change')"
              />
            </th>
            <th class="px-1 pb-1 font-semibold">Oferta</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(_origen, i) in problema.origenes" :key="`row-${i}`">
            <td class="pr-1">
              <input
                :value="problema.origenes[i]"
                :class="headerFieldClass"
                @change="problema.origenes[i] = $event.target.value; emit('change')"
              />
            </td>
            <td v-for="(_destino, j) in problema.destinos" :key="`c-${i}-${j}`" class="p-0.5">
              <input
                :ref="(el) => registrarCelda(refClave(`c-${i}-${j}`), el)"
                type="text" inputmode="decimal"
                :value="problema.costos[i][j]"
                :class="cellFieldClass"
                @change="problema.costos[i][j] = Number($event.target.value) || 0; emit('change')"
                @keydown.enter="mover(refClave(`c-${i}-${j}`), 1, $event)"
                @keydown.down="mover(refClave(`c-${i}-${j}`), 1, $event)"
                @keydown.up="mover(refClave(`c-${i}-${j}`), -1, $event)"
              />
            </td>
            <td class="p-0.5">
              <input
                type="text" inputmode="decimal"
                :value="problema.oferta[i]"
                :class="cellFieldClass"
                @change="problema.oferta[i] = Number($event.target.value) || 0; emit('change')"
              />
            </td>
          </tr>
          <tr>
            <td class="pr-1 text-right font-semibold">Demanda</td>
            <td v-for="(_destino, j) in problema.destinos" :key="`dm-${j}`" class="p-0.5">
              <input
                type="text" inputmode="decimal"
                :value="problema.demanda[j]"
                :class="cellFieldClass"
                @change="problema.demanda[j] = Number($event.target.value) || 0; emit('change')"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
