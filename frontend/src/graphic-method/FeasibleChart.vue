<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LineChart, ScatterChart } from 'echarts/charts'
import { DataZoomInsideComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

import { formatNumber } from './format'

use([
  LineChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomInsideComponent,
  CanvasRenderer,
])

const props = defineProps({
  result: { type: Object, required: true },
  showObjective: { type: Boolean, default: true },
})

const container = ref(null)
const palette = ['#818cf8', '#f472b6', '#38bdf8', '#fbbf24', '#34d399', '#c084fc', '#fb7185', '#2dd4bf']

let chart = null
let resizeObserver = null

function pointTooltip(result, index) {
  const point = result.points[index]
  if (!point) return ''
  const status = point.optimal ? 'Solución óptima' : point.feasible ? 'Factible' : 'No factible'
  return [
    `<div style="font-weight:600;margin-bottom:4px">${point.label} · ${status}</div>`,
    `x₁ = ${formatNumber(point.x1)} &nbsp;&nbsp; x₂ = ${formatNumber(point.x2)}`,
    `<div style="margin-top:4px">Z = ${formatNumber(point.z)}</div>`,
    `<div style="margin-top:4px;color:#a3a3a3">${point.sources.join(' · ')}</div>`,
  ].join('')
}

function buildOption(result, showObjective) {
  const plot = result.region?.plot ?? { xMax: 10, yMax: 10 }
  const series = []
  const legendData = result.lines.map((line) => line.label)

  if (result.region?.type === 'area' && result.region.polygon?.length >= 3) {
    const polygon = [...result.region.polygon, result.region.polygon[0]]
    series.push({
      name: 'Región factible',
      type: 'line',
      data: polygon,
      symbol: 'none',
      silent: true,
      z: 1,
      lineStyle: { color: '#10b981', width: 1.5, opacity: 0.55 },
      areaStyle: { color: 'rgba(16, 185, 129, 0.18)' },
      tooltip: { show: false },
      emphasis: { disabled: true },
    })
  }

  if (result.region?.type === 'segment' && result.region.segment?.length === 2) {
    series.push({
      name: 'Región factible',
      type: 'line',
      data: result.region.segment,
      symbol: 'none',
      silent: true,
      z: 1,
      lineStyle: { color: '#34d399', width: 8, opacity: 0.55 },
      tooltip: { show: false },
      emphasis: { disabled: true },
    })
  }

  if (result.region?.type === 'point' && result.region.point) {
    series.push({
      name: 'Región factible',
      type: 'scatter',
      data: [result.region.point],
      symbol: 'circle',
      symbolSize: 18,
      itemStyle: { color: 'rgba(52, 211, 153, 0.35)', borderColor: '#34d399', borderWidth: 2 },
      silent: true,
      z: 1,
      tooltip: { show: false },
    })
  }

  result.lines.forEach((line, index) => {
    series.push({
      name: line.label,
      type: 'line',
      data: line.points,
      symbol: 'none',
      z: 3,
      lineStyle: { width: 2.2, color: palette[index % palette.length] },
      emphasis: { focus: 'series', lineStyle: { width: 3.5 } },
    })
  })

  if (showObjective && result.objective_line?.points?.length === 2) {
    legendData.push('Recta objetivo')
    series.push({
      name: 'Recta objetivo',
      type: 'line',
      data: result.objective_line.points,
      symbol: 'none',
      z: 2,
      lineStyle: { width: 2, type: 'dashed', color: '#fbbf24' },
      emphasis: { focus: 'series', lineStyle: { width: 3.2 } },
    })
  }

  const points = result.points.map((point) => ({
    name: point.label,
    value: [point.x1, point.x2],
    symbol: point.optimal ? 'star' : 'circle',
    symbolSize: point.optimal ? 20 : point.feasible ? 11 : 7,
    itemStyle: {
      color: point.optimal ? '#34d399' : point.feasible ? '#60a5fa' : '#64748b',
      borderColor: point.optimal ? '#a7f3d0' : '#0f172a',
      borderWidth: 1.5,
      opacity: point.feasible ? 1 : 0.65,
    },
    label: {
      show: true,
      position: 'top',
      formatter: point.optimal ? `${point.label} ★` : point.label,
      color: point.optimal ? '#a7f3d0' : point.feasible ? '#bfdbfe' : '#64748b',
      fontSize: point.optimal ? 12 : 10,
      fontWeight: point.optimal ? 600 : 400,
    },
  }))

  legendData.push('Puntos de intersección')
  series.push({
    name: 'Puntos de intersección',
    type: 'scatter',
    data: points,
    z: 5,
    emphasis: { scale: 1.4 },
    labelLayout: { hideOverlap: true },
  })

  return {
    backgroundColor: 'transparent',
    animationDuration: 300,
    color: palette,
    grid: { left: 62, right: 26, top: 30, bottom: 82 },
    legend: {
      type: 'scroll',
      bottom: 2,
      data: legendData,
      textStyle: { color: '#a3a3a3' },
      inactiveColor: '#525252',
      itemWidth: 16,
      itemHeight: 8,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 10, 10, 0.94)',
      borderColor: '#3f3f46',
      textStyle: { color: '#f5f5f5', fontSize: 12 },
      formatter(params) {
        if (params.seriesName === 'Puntos de intersección') {
          return pointTooltip(result, params.dataIndex)
        }
        if (params.seriesName === 'Recta objetivo') {
          return `<b>Recta objetivo</b><br/>Z = ${formatNumber(result.objective_line.z)}`
        }
        const line = result.lines.find((item) => item.label === params.seriesName)
        if (line) return `<b>${line.label}</b><br/>${line.equation}`
        return params.seriesName
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: plot.xMax,
      name: 'x₁',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: '#d4d4d4', fontWeight: 600 },
      axisLabel: { color: '#737373' },
      axisLine: { lineStyle: { color: '#525252' } },
      splitLine: { lineStyle: { color: '#262626' } },
      axisPointer: { lineStyle: { color: '#6366f1' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: plot.yMax,
      name: 'x₂',
      nameLocation: 'middle',
      nameGap: 44,
      nameTextStyle: { color: '#d4d4d4', fontWeight: 600 },
      axisLabel: { color: '#737373' },
      axisLine: { lineStyle: { color: '#525252' } },
      splitLine: { lineStyle: { color: '#262626' } },
      axisPointer: { lineStyle: { color: '#6366f1' } },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
    ],
    series,
  }
}

function render() {
  if (!chart || !props.result) return
  chart.setOption(buildOption(props.result, props.showObjective), true)
}

function resetZoom() {
  render()
}

onMounted(() => {
  chart = init(container.value)
  render()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(container.value)
  } else {
    window.addEventListener('resize', handleResize)
  }
})

function handleResize() {
  chart?.resize()
}

watch(() => props.result, render)
watch(() => props.showObjective, render)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="relative">
    <div ref="container" class="h-[420px] w-full lg:h-[540px]" />
    <button
      type="button"
      class="absolute right-3 top-3 rounded-md border border-neutral-700 bg-neutral-950/80 px-2.5 py-1.5 text-xs text-neutral-300 backdrop-blur transition hover:border-indigo-500 hover:text-white"
      @click="resetZoom"
    >
      Restablecer vista
    </button>
    <p class="pointer-events-none absolute bottom-20 left-16 text-[10px] text-neutral-600">
      Rueda para zoom · arrastra para mover
    </p>
  </div>
</template>
