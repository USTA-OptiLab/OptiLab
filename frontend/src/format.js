// Formato numérico compartido: enteros sin decimales, el resto con `decimales`.
export function num(x, decimales = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return ''
  if (Math.abs(x - Math.round(x)) < 1e-9) return String(Math.round(x))
  return Number(x).toFixed(decimales)
}

// Números negativos entre paréntesis, para ecuaciones como "30 − 0 − (−12)".
export function conParentesis(x, decimales = 2) {
  return x < 0 ? `(${num(x, decimales).replace('-', '−')})` : num(x, decimales)
}

export const NOMBRES_METODO = {
  vogel: 'Aproximación de Vogel',
  costo_minimo: 'Costo mínimo',
  noroeste: 'Esquina noroeste',
}
