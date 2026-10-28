<script setup>
import { computed } from 'vue'

const props = defineProps({
  problema: { type: Object, required: true },
  iteracion: { type: Object, required: true },
  decimales: { type: Number, default: 2 },
  epsilon: { type: Number, default: 1e-9 },
  titulo: { type: String, default: '' },
})

const COLOR = {
  azul: '#2e5d9f',
  azulBasica: '#dbe6f5',
  verde: '#1e8449',
  rojo: '#c0392b',
  texto: '#111111',
}

const WIDTH = 760
const HEIGHT = 480
const X_O = 130
const X_D = WIDTH - 130
const TOP = 60
const BOTTOM = HEIGHT - 60

function num(x) {
  if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x))
  return Number(x).toFixed(props.decimales)
}

function yDe(k, total) {
  return TOP + ((BOTTOM - TOP) * (k + 0.5)) / total
}

const yo = computed(() => props.problema.origenes.map((_, i) => yDe(i, props.problema.m)))
const yd = computed(() => props.problema.destinos.map((_, j) => yDe(j, props.problema.n)))

const signos = computed(() => {
  const m = new Map()
  for (const [i, j, s] of props.iteracion.ciclo) m.set(`${i},${j}`, s)
  return m
})

const maximo = computed(() => Math.max(...props.iteracion.asignacion.flat(), 1e-9))

const aristas = computed(() => {
  const lista = []
  const entrante = props.iteracion.entrante
  for (let i = 0; i < props.problema.m; i++) {
    for (let j = 0; j < props.problema.n; j++) {
      const cantidad = props.iteracion.asignacion[i][j]
      const esEntrante = entrante && entrante[0] === i && entrante[1] === j
      const enCiclo = signos.value.has(`${i},${j}`)
      if (esEntrante) lista.push({ i, j, cantidad, tipo: 'entra' })
      else if (cantidad > props.epsilon || enCiclo) lista.push({ i, j, cantidad, tipo: enCiclo ? 'ciclo' : 'normal' })
    }
  }
  lista.sort((a, b) => (a.tipo !== 'normal') - (b.tipo !== 'normal'))
  return lista
})

function colorArista(a) {
  if (props.iteracion.sale && props.iteracion.sale[0] === a.i && props.iteracion.sale[1] === a.j) return COLOR.rojo
  if (a.tipo === 'entra') return COLOR.verde
  if (a.tipo === 'ciclo') return signos.value.get(`${a.i},${a.j}`) > 0 ? COLOR.verde : COLOR.rojo
  return COLOR.azul
}

function anchoArista(a) {
  if (a.tipo === 'entra') return 3
  return 1 + (11 * a.cantidad) / maximo.value
}

function etiquetaArista(a) {
  if (a.tipo === 'entra') return 'entra'
  const base = num(a.cantidad)
  if (a.tipo === 'ciclo') return `${base} ${signos.value.get(`${a.i},${a.j}`) > 0 ? '(+)' : '(−)'}`
  return base
}

function puntoMedio(a) {
  const x = X_O + 14 + (X_D - X_O - 28) * (0.35 + (0.3 * ((a.i + a.j) % 3)) / 2)
  const y = yo.value[a.i] + ((yd.value[a.j] - yo.value[a.i]) * (x - X_O - 14)) / (X_D - X_O - 28)
  return { x, y }
}
</script>

<template>
  <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="h-full w-full font-sans" role="img">
    <text x="12" y="20" font-size="13" font-weight="600" :fill="COLOR.texto">{{ titulo }}</text>

    <defs>
      <marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" :fill="COLOR.azul" />
      </marker>
    </defs>

    <g v-for="a in aristas" :key="`${a.i}-${a.j}`">
      <line
        :x1="X_O + 14" :y1="yo[a.i]" :x2="X_D - 14" :y2="yd[a.j]"
        :stroke="colorArista(a)" :stroke-width="anchoArista(a)"
        :stroke-dasharray="a.tipo === 'entra' ? '6,4' : undefined"
        marker-end="url(#flecha)"
      />
      <rect :x="puntoMedio(a).x - 22" :y="puntoMedio(a).y - 9" width="44" height="14" fill="white" opacity="0.85" />
      <text :x="puntoMedio(a).x" :y="puntoMedio(a).y + 2" text-anchor="middle" font-size="10" font-weight="600" :fill="colorArista(a)">{{ etiquetaArista(a) }}</text>
    </g>

    <g v-for="(origen, i) in problema.origenes" :key="`o-${i}`">
      <circle :cx="X_O" :cy="yo[i]" r="14" :fill="COLOR.azulBasica" :stroke="COLOR.azul" stroke-width="2" />
      <text :x="X_O - 22" :y="yo[i] - 2" text-anchor="end" font-size="10" :fill="COLOR.texto">{{ origen }}</text>
      <text :x="X_O - 22" :y="yo[i] + 11" text-anchor="end" font-size="10" :fill="COLOR.texto">oferta {{ num(problema.oferta[i]) }}</text>
    </g>
    <g v-for="(destino, j) in problema.destinos" :key="`d-${j}`">
      <circle :cx="X_D" :cy="yd[j]" r="14" :fill="COLOR.azulBasica" :stroke="COLOR.azul" stroke-width="2" />
      <text :x="X_D + 22" :y="yd[j] - 2" font-size="10" :fill="COLOR.texto">{{ destino }}</text>
      <text :x="X_D + 22" :y="yd[j] + 11" font-size="10" :fill="COLOR.texto">demanda {{ num(problema.demanda[j]) }}</text>
    </g>

    <g :transform="`translate(12, ${HEIGHT - 20})`">
      <rect width="14" height="14" :fill="COLOR.azul" />
      <text x="20" y="11" font-size="10" :fill="COLOR.texto">envío</text>
      <rect x="90" width="14" height="14" :fill="COLOR.verde" />
      <text x="110" y="11" font-size="10" :fill="COLOR.texto">entra / ciclo +</text>
      <rect x="230" width="14" height="14" :fill="COLOR.rojo" />
      <text x="250" y="11" font-size="10" :fill="COLOR.texto">ciclo −</text>
    </g>
    <text :x="WIDTH - 12" :y="HEIGHT - 9" text-anchor="end" font-size="10" :fill="COLOR.texto">Costo total = {{ num(iteracion.costo) }}</text>
  </svg>
</template>
