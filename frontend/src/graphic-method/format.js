export const OP_OPTIONS = [
  { value: '<=', label: '≤' },
  { value: '>=', label: '≥' },
  { value: '=', label: '=' },
]

const OP_LABELS = Object.fromEntries(OP_OPTIONS.map((option) => [option.value, option.label]))

export function formatNumber(value, digits = 6) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  if (Math.abs(number) < 1e-12) return '0'
  return String(Number(number.toFixed(digits)))
}

function formatTerm(coefficient, variable, first) {
  const number = Number(coefficient)
  if (!Number.isFinite(number) || Math.abs(number) < 1e-9) return ''

  const magnitude = Math.abs(number)
  const prefix = Math.abs(magnitude - 1) < 1e-9 ? '' : formatNumber(magnitude)
  const term = `${prefix}${variable}`

  if (first) return number < 0 ? `-${term}` : term
  return number < 0 ? `- ${term}` : `+ ${term}`
}

export function formatTerms(c1, c2) {
  const first = formatTerm(c1, 'x₁', true)
  const second = formatTerm(c2, 'x₂', !first)
  return [first, second].filter(Boolean).join(' ') || '0'
}

export function formatConstraint(constraint) {
  const empty = [constraint.a1, constraint.a2, constraint.b].some(
    (value) => value === null || value === undefined || String(value).trim() === '',
  )
  if (empty) return 'Completa los coeficientes'
  const op = OP_LABELS[constraint.op] ?? constraint.op ?? '?'
  return `${formatTerms(constraint.a1, constraint.a2)} ${op} ${formatNumber(constraint.b)}`
}

export function formatPoint(point) {
  return `(${formatNumber(point.x1)}, ${formatNumber(point.x2)})`
}
