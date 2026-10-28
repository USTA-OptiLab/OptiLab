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
  verdeClaro: '#cfe8cf',
  rojoClaro: '#f4c7c3',
  verdeEntra: '#7fc97f',
  azulBasica: '#dbe6f5',
  blanco: '#ffffff',
  gris: '#8a8a8a',
  texto: '#111111',
  rojo: '#c0392b',
  verde: '#1e8449',
  azul: '#2e5d9f',
}

const CELL_W = 118
const CELL_H = 62
const LEFT = 108
const TOP = 46

function num(x) {
  if (x === null || x === undefined) return ''
  if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x))
  return Number(x).toFixed(props.decimales)
}

const signos = computed(() => {
  const m = new Map()
  for (const [i, j, s] of props.iteracion.ciclo) m.set(`${i},${j}`, s)
  return m
})
const basicas = computed(() => new Set(props.iteracion.basicas.map(([i, j]) => `${i},${j}`)))

function estilo(i, j) {
  const key = `${i},${j}`
  const entrante = props.iteracion.entrante
  if (entrante && entrante[0] === i && entrante[1] === j) {
    return { fill: COLOR.verdeEntra, stroke: COLOR.verde, width: 3 }
  }
  const s = signos.value.get(key)
  if (s > 0) return { fill: COLOR.verdeClaro, stroke: COLOR.verde, width: 2 }
  if (s < 0) return { fill: COLOR.rojoClaro, stroke: COLOR.rojo, width: 2 }
  return { fill: basicas.value.has(key) ? COLOR.azulBasica : COLOR.blanco, stroke: COLOR.gris, width: 1 }
}

function esSalida(i, j) {
  const s = props.iteracion.sale
  return !!s && s[0] === i && s[1] === j
}

const width = computed(() => LEFT + CELL_W * props.problema.n + 70)
const height = computed(() => TOP + CELL_H * props.problema.m + 150)
const leyenda = [
  { color: COLOR.verdeEntra, texto: 'entra' },
  { color: COLOR.verdeClaro, texto: 'ciclo +' },
  { color: COLOR.rojoClaro, texto: 'ciclo −' },
  { color: COLOR.azulBasica, texto: 'básica' },
  { color: COLOR.blanco, texto: 'no básica (Δ)' },
]
</script>

<template>
  <svg :viewBox="`0 0 ${width} ${height}`" class="h-full w-full rounded bg-white font-sans" role="img">
    <text x="12" y="20" font-size="13" font-weight="600" :fill="COLOR.texto">{{ titulo }}</text>

    <text
      v-for="(destino, j) in problema.destinos"
      :key="`d-${j}`"
      :x="LEFT + CELL_W * (j + 0.5)"
      :y="TOP - 10"
      text-anchor="middle"
      font-size="11"
      font-weight="700"
      :fill="COLOR.texto"
    >{{ destino }}</text>
    <text :x="LEFT + CELL_W * problema.n + 10" :y="TOP - 10" font-size="11" font-weight="700" :fill="COLOR.texto">Oferta</text>
    <text :x="LEFT - 10" :y="TOP + CELL_H * problema.m + 16" text-anchor="end" font-size="11" font-weight="700" :fill="COLOR.texto">Demanda</text>

    <g v-for="(origen, i) in problema.origenes" :key="`o-${i}`">
      <text :x="LEFT - 10" :y="TOP + CELL_H * (i + 0.5) + 4" text-anchor="end" font-size="11" font-weight="700" :fill="COLOR.texto">{{ origen }}</text>
      <text :x="LEFT + CELL_W * problema.n + 10" :y="TOP + CELL_H * (i + 0.5) + 4" font-size="11" :fill="COLOR.texto">{{ num(problema.oferta[i]) }}</text>

      <g v-for="(_destino, j) in problema.destinos" :key="`c-${i}-${j}`">
        <rect
          :x="LEFT + CELL_W * j"
          :y="TOP + CELL_H * i"
          :width="CELL_W"
          :height="CELL_H"
          :fill="estilo(i, j).fill"
          :stroke="estilo(i, j).stroke"
          :stroke-width="estilo(i, j).width"
        />
        <text :x="LEFT + CELL_W * j + 6" :y="TOP + CELL_H * i + 14" font-size="9" :fill="COLOR.gris">c={{ num(problema.costos[i][j]) }}</text>

        <text
          v-if="basicas.has(`${i},${j}`)"
          :x="LEFT + CELL_W * j + CELL_W / 2"
          :y="TOP + CELL_H * i + CELL_H / 2 + 6"
          text-anchor="middle"
          font-size="16"
          font-weight="700"
          :fill="COLOR.texto"
        >{{ num(iteracion.asignacion[i][j]) }}</text>
        <text
          v-else
          :x="LEFT + CELL_W * j + CELL_W / 2"
          :y="TOP + CELL_H * i + CELL_H / 2 + 6"
          text-anchor="middle"
          font-size="12"
          :fill="iteracion.delta[i][j] < -epsilon ? COLOR.rojo : COLOR.gris"
        >Δ={{ num(iteracion.delta[i][j]) }}</text>

        <text
          v-if="signos.get(`${i},${j}`)"
          :x="LEFT + CELL_W * j + CELL_W - 8"
          :y="TOP + CELL_H * i + 14"
          text-anchor="end"
          font-size="15"
          font-weight="700"
          :fill="signos.get(`${i},${j}`) > 0 ? COLOR.verde : COLOR.rojo"
        >{{ signos.get(`${i},${j}`) > 0 ? '+' : '−' }}</text>

        <text
          v-if="iteracion.entrante && iteracion.entrante[0] === i && iteracion.entrante[1] === j"
          :x="LEFT + CELL_W * j + CELL_W / 2"
          :y="TOP + CELL_H * i + CELL_H - 6"
          text-anchor="middle"
          font-size="9"
          font-weight="700"
          :fill="COLOR.verde"
        >entra</text>
        <text
          v-else-if="esSalida(i, j)"
          :x="LEFT + CELL_W * j + CELL_W / 2"
          :y="TOP + CELL_H * i + CELL_H - 6"
          text-anchor="middle"
          font-size="9"
          font-weight="700"
          :fill="COLOR.rojo"
        >sale</text>
      </g>
    </g>

    <text
      v-for="(demanda, j) in problema.demanda"
      :key="`dm-${j}`"
      :x="LEFT + CELL_W * (j + 0.5)"
      :y="TOP + CELL_H * problema.m + 16"
      text-anchor="middle"
      font-size="11"
      :fill="COLOR.texto"
    >{{ num(demanda) }}</text>

    <g :transform="`translate(12, ${TOP + CELL_H * problema.m + 40})`">
      <g v-for="(item, k) in leyenda" :key="item.texto" :transform="`translate(${k * 118}, 0)`">
        <rect width="14" height="14" :fill="item.color" :stroke="COLOR.gris" />
        <text x="20" y="11" font-size="10" :fill="COLOR.texto">{{ item.texto }}</text>
      </g>
    </g>

    <text
      :x="12"
      :y="TOP + CELL_H * problema.m + 70"
      font-size="11"
      :fill="iteracion.entrante ? COLOR.texto : COLOR.verde"
      :font-weight="iteracion.entrante ? 400 : 700"
    >{{ iteracion.entrante ? `θ = ${num(iteracion.theta)}  (se suma θ en las celdas + y se resta en las −)` : 'Todos los Δ ≥ 0: solución óptima' }}</text>
  </svg>
</template>
