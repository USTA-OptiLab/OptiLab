<script setup>
import { computed } from 'vue'
import { NOMBRES_METODO, num } from '../format.js'

const props = defineProps({
  resultado: { type: Object, required: true },
  opciones: { type: Object, required: true },
})

const EPS = 1e-9
const b = (x) => ({ b: String(x) })

function lista(items) {
  if (items.length <= 1) return items.join('')
  return `${items.slice(0, -1).join(', ')} y ${items[items.length - 1]}`
}

// Cada ítem es un arreglo de fragmentos: texto plano o { b } para resaltar.
const secciones = computed(() => {
  const r = props.resultado
  const p = r.problema
  const dec = props.opciones.decimales
  const n = (x) => num(x, dec)
  const maximizar = props.opciones.modo === 'maximizar'
  const medida = maximizar ? 'ganancia' : 'costo'
  const fF = r.fila_ficticia
  const cF = r.columna_ficticia
  const final = r.historial[r.historial.length - 1]
  const x = final.asignacion

  const origenes = p.origenes.map((nombre, i) => i).filter((i) => i !== fF)
  const destinos = p.destinos.map((nombre, j) => j).filter((j) => j !== cF)
  const ofertaTotal = origenes.reduce((s, i) => s + p.oferta[i], 0)
  const demandaTotal = destinos.reduce((s, j) => s + p.demanda[j], 0)

  const rutas = []
  for (const i of origenes) {
    for (const j of destinos) {
      if (x[i][j] > EPS) rutas.push({ i, j, q: x[i][j], c: p.costos[i][j], sub: x[i][j] * p.costos[i][j] })
    }
  }
  const unidades = rutas.reduce((s, ru) => s + ru.q, 0)
  const nombreRuta = (i, j) => `${p.origenes[i]} → ${p.destinos[j]}`

  const out = []

  // 1. Planteamiento
  const plan = [
    [
      'El problema busca ', b(maximizar ? 'maximizar la ganancia total' : 'minimizar el costo total'),
      ` de enviar mercancía desde ${origenes.length} origen(es) (${lista(origenes.map((i) => p.origenes[i]))}) hacia ${destinos.length} destino(s) (${lista(destinos.map((j) => p.destinos[j]))}).`,
    ],
    ['La oferta total es ', b(n(ofertaTotal)), ' y la demanda total es ', b(n(demandaTotal)), '.'],
  ]
  if (cF !== null) {
    plan.push([`Como la oferta supera a la demanda en ${n(ofertaTotal - demandaTotal)} unidades, se agregó un destino ficticio con costo 0 que absorbe ese excedente: representa capacidad que no se utiliza.`])
  } else if (fF !== null) {
    plan.push([`Como la demanda supera a la oferta en ${n(demandaTotal - ofertaTotal)} unidades, se agregó un origen ficticio con costo 0: representa demanda que no se alcanza a cubrir.`])
  } else {
    plan.push(['El problema está balanceado: toda la oferta se despacha y toda la demanda se cubre.'])
  }
  out.push({ titulo: 'Planteamiento', color: 'text-sky-300', items: plan })

  // 2. Plan de envíos
  const envios = []
  for (const i of origenes) {
    const destinosDe = destinos.filter((j) => x[i][j] > EPS).map((j) => `${n(x[i][j])} a ${p.destinos[j]}`)
    const sinUsar = cF !== null ? x[i][cF] : 0
    const frase = [b(p.origenes[i]), ` (oferta ${n(p.oferta[i])}): `]
    frase.push(destinosDe.length ? ['envía ', b(lista(destinosDe))] : ['no envía nada'])
    if (sinUsar > EPS) frase.push(`, y deja ${n(sinUsar)} unidades sin usar.`)
    else frase.push('.')
    envios.push(frase.flat())
  }
  if (fF !== null) {
    for (const j of destinos) {
      if (x[fF][j] > EPS) envios.push([b(p.destinos[j]), ` queda con ${n(x[fF][j])} unidades sin cubrir de su demanda de ${n(p.demanda[j])}.`])
    }
  }
  out.push({ titulo: r.optimo ? 'Plan óptimo de envíos' : 'Mejor plan encontrado', color: 'text-indigo-300', items: envios })

  // 3. Costos
  const costos = [[`El ${medida} total es `, b(n(r.costo)), unidades > EPS ? ` para ${n(unidades)} unidades enviadas, es decir ${n(r.costo / unidades)} por unidad en promedio.` : '.']]
  if (rutas.length) {
    const mayorUso = rutas.reduce((a, c) => (c.q > a.q ? c : a))
    const mayorAporte = rutas.reduce((a, c) => (c.sub > a.sub ? c : a))
    costos.push(['La ruta más usada es ', b(nombreRuta(mayorUso.i, mayorUso.j)), ` con ${n(mayorUso.q)} unidades (${Math.round((100 * mayorUso.q) / unidades)}% del total enviado).`])
    if (r.costo > EPS) costos.push(['La ruta que más pesa en el ', medida, ' es ', b(nombreRuta(mayorAporte.i, mayorAporte.j)), `: aporta ${n(mayorAporte.sub)} (${Math.round((100 * mayorAporte.sub) / r.costo)}%).`])
  }
  const mejora = maximizar ? r.costo - r.costo_inicial : r.costo_inicial - r.costo
  if (r.mejoras > 0 && mejora > EPS) {
    costos.push([
      `El método ${NOMBRES_METODO[props.opciones.metodo_inicial]} dio un ${medida} inicial de ${n(r.costo_inicial)}; MODI lo mejoró a `, b(n(r.costo)),
      ` en ${r.mejoras} iteración(es): ${maximizar ? 'ganancia adicional' : 'ahorro'} de ${n(mejora)} (${Math.round((100 * mejora) / Math.abs(r.costo_inicial))}%).`,
    ])
  } else if (r.optimo) {
    costos.push([`La solución inicial (${NOMBRES_METODO[props.opciones.metodo_inicial]}) ya era óptima: no hubo nada que mejorar.`])
  }
  out.push({ titulo: medida === 'costo' ? 'Costos' : 'Ganancias', color: 'text-emerald-300', items: costos })

  // 4. Sensibilidad básica (solo con solución óptima)
  if (r.optimo) {
    const basicas = new Set(final.basicas.map(([i, j]) => `${i},${j}`))
    const noBasicas = []
    for (const i of origenes) {
      for (const j of destinos) {
        if (!basicas.has(`${i},${j}`)) noBasicas.push({ i, j, d: final.delta[i][j], c: p.costos[i][j] })
      }
    }
    const sens = []
    const alternativas = noBasicas.filter((f) => Math.abs(f.d) <= EPS)
    for (const f of alternativas) {
      sens.push([b(nombreRuta(f.i, f.j)), ' tiene Δ = 0: puede usarse sin alterar el valor total, lo que da una solución alternativa.'])
    }
    const candidatas = noBasicas.filter((f) => f.d > EPS).sort((a, c) => a.d - c.d).slice(0, 3)
    for (const f of candidatas) {
      const umbral = maximizar ? f.c + f.d : f.c - f.d
      sens.push([
        b(nombreRuta(f.i, f.j)), ` no se usa hoy. Entraría al plan si su ${medida} ${maximizar ? 'subiera de' : 'bajara de'} ${n(f.c)} a ${maximizar ? 'más' : 'menos'} de ${n(umbral)}.`,
      ])
    }
    if (sens.length) out.push({ titulo: 'Qué pasaría si cambian los parámetros', color: 'text-amber-300', items: sens })
  }

  // 5. Observaciones
  const obs = []
  const positivas = final.basicas.filter(([i, j]) => x[i][j] > EPS).length
  if (positivas < final.basicas.length) obs.push(['La solución es degenerada: alguna celda básica tiene asignación 0.'])
  if (!r.optimo) obs.push([`El algoritmo se detuvo al alcanzar el máximo de ${props.opciones.max_iteraciones} iteraciones; aumenta ese límite para confirmar la optimalidad.`])
  if (r.optimo && r.optimos_alternativos) obs.push(['Hay más de un plan óptimo con el mismo valor: puedes elegir el que mejor se ajuste a criterios que no están en el modelo.'])
  if (obs.length) out.push({ titulo: 'Observaciones', color: 'text-rose-300', items: obs })

  return out
})
</script>

<template>
  <section class="rounded-xl border border-neutral-800 bg-neutral-900/30">
    <header class="flex items-center gap-3 border-b border-neutral-800 px-4 py-3">
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-sky-500 text-sm font-bold text-sky-950">i</span>
      <h3 class="text-lg font-semibold">Interpretación del problema</h3>
    </header>
    <div class="grid gap-4 p-4 lg:grid-cols-2">
      <div v-for="s in secciones" :key="s.titulo" class="rounded-lg border border-neutral-800 bg-neutral-900/50 p-4">
        <h4 class="mb-2 font-semibold" :class="s.color">{{ s.titulo }}</h4>
        <ul class="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-neutral-300 marker:text-neutral-600">
          <li v-for="(item, k) in s.items" :key="k">
            <template v-for="(parte, q) in item" :key="q">
              <strong v-if="typeof parte === 'object'" class="text-neutral-100">{{ parte.b }}</strong>
              <template v-else>{{ parte }}</template>
            </template>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
