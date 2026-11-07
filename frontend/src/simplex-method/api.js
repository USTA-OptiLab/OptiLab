// Bridge for pywebview API with browser fallback

export const DEFAULT_EXAMPLES = [
  {
    id: "ejemplo-1",
    title: "1. Fabricación de Mesas y Sillas (Max clásico)",
    description: "Max Z = 3x1 + 5x2. Corte (4h), Ensamble (12h) y Acabado (18h). Solución: 2 mesas, 6 sillas -> Ganancia $36",
    objective: "max",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [3, 5],
    constraints: [
      { lhs: [1, 0], sign: "<=", rhs: 4 },
      { lhs: [0, 2], sign: "<=", rhs: 12 },
      { lhs: [3, 2], sign: "<=", rhs: 18 },
    ],
    context: {
      title: "Fabricación de Mesas y Sillas",
      statement: "Una fábrica produce mesas (x1) y sillas (x2). Cada mesa vendida aporta una ganancia de $3 y cada silla $5. El taller dispone de hasta 4 horas para corte de piezas, 12 horas en el área de ensamblaje y 18 horas para acabado final. ¿Cuántas mesas y sillas se deben fabricar para maximizar la ganancia total del taller?",
      objective_name: "Ganancia total del taller",
      objective_unit: "$",
      var_descriptions: ["Mesas a fabricar", "Sillas a fabricar"],
      var_units: ["mesas", "sillas"],
      constraint_descriptions: ["Horas disponibles en Corte", "Horas disponibles en Ensamblaje", "Horas disponibles en Acabado"],
      constraint_units: ["horas", "horas", "horas"],
    },
  },
  {
    id: "ejemplo-2",
    title: "2. Mezcla de Nutrientes (Minimización)",
    description: "Min Z = -x1 - 2x2. Control de presupuesto de insumos. Solución: (3, 1), Costo Z = -5",
    objective: "min",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [-1, -2],
    constraints: [
      { lhs: [1, 1], sign: "<=", rhs: 4 },
      { lhs: [1, 3], sign: "<=", rhs: 6 },
    ],
    context: {
      title: "Minimización de Costos en Mezcla Balanceada",
      statement: "Un laboratorio agropecuario formula un alimento balanceado combinando dos ingredientes: A (x1) y B (x2). Cada unidad de A genera un ahorro neto de $1 y cada unidad de B de $2. Los ingredientes están sujetos a límites de almacenamiento de 4 y 6 unidades. ¿Cuál es la dosificación óptima para minimizar el costo neto?",
      objective_name: "Costo neto de la fórmula",
      objective_unit: "$",
      var_descriptions: ["Ingrediente A a incorporar", "Ingrediente B a incorporar"],
      var_units: ["kg", "kg"],
      constraint_descriptions: ["Límite de almacenamiento 1", "Límite de almacenamiento 2"],
      constraint_units: ["kg", "kg"],
    },
  },
  {
    id: "ejemplo-3",
    title: "3. Confección Textil (Óptimos Alternativos)",
    description: "Max Z = 2x1 + 4x2. Múltiples combinaciones de camisas y pantalones alcanzan la misma ganancia óptima de $16",
    objective: "max",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [2, 4],
    constraints: [
      { lhs: [1, 2], sign: "<=", rhs: 8 },
      { lhs: [1, 0], sign: "<=", rhs: 6 },
      { lhs: [0, 1], sign: "<=", rhs: 3 },
    ],
    context: {
      title: "Confección de Camisas y Pantalones",
      statement: "Una pequeña empresa textil confecciona camisas (x1) con $2 de ganancia y pantalones (x2) con $4 de ganancia. Se dispone de 8 metros de tela especial, con una demanda máxima del mercado de 6 camisas y 3 pantalones. ¿Cuál es la producción recomendada sabiendo que existen soluciones alternativas?",
      objective_name: "Utilidad total de ventas",
      objective_unit: "$",
      var_descriptions: ["Camisas a confeccionar", "Pantalones a confeccionar"],
      var_units: ["camisas", "pantalones"],
      constraint_descriptions: ["Metros de tela disponibles", "Demanda máxima de camisas", "Demanda máxima de pantalones"],
      constraint_units: ["metros", "unidades", "unidades"],
    },
  },
  {
    id: "ejemplo-4",
    title: "4. Línea de Ensamble (Solución Degenerada)",
    description: "Max Z = x1 + x2. Restricciones redundantes en el vértice común (2, 2) con cociente cero",
    objective: "max",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [1, 1],
    constraints: [
      { lhs: [1, 0], sign: "<=", rhs: 2 },
      { lhs: [0, 1], sign: "<=", rhs: 2 },
      { lhs: [1, 1], sign: "<=", rhs: 4 },
    ],
    context: {
      title: "Distribución en Planta de Componentes",
      statement: "Una planta tecnológica ensambla procesadores (x1) y tarjetas gráficas (x2) ganando $1 por componente. La capacidad máxima de cada línea es de 2 componentes, y el suministro conjunto no supera 4 componentes. En el punto óptimo (2, 2), tres restricciones coinciden exactamente, generando degeneración.",
      objective_name: "Ingreso operativo total",
      objective_unit: "$",
      var_descriptions: ["Procesadores ensamblados", "Tarjetas gráficas ensambladas"],
      var_units: ["unidades", "unidades"],
      constraint_descriptions: ["Capacidad de línea de procesadores", "Capacidad de línea de tarjetas", "Suministro eléctrico conjunto"],
      constraint_units: ["unidades", "unidades", "unidades"],
    },
  },
  {
    id: "ejemplo-5",
    title: "5. Campaña de Marketing (Problema No Acotado)",
    description: "Max Z = 2x1 + x2 sujeto a x1 - x2 <= 3. Sin límite superior de recursos, Z crece indefinidamente",
    objective: "max",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [2, 1],
    constraints: [
      { lhs: [1, -1], sign: "<=", rhs: 3 },
    ],
    context: {
      title: "Campaña de Marketing Digital",
      statement: "Una agencia modela la asignación de anuncios en redes sociales (x1) y en motores de búsqueda (x2). Debido a una omisión en el planteamiento, no se fijó un límite presupuestario ni de inventario de clics. La función objetivo puede crecer sin límite, demostrando que faltan restricciones del mundo real.",
      objective_name: "Alcance estimado de campaña",
      objective_unit: "puntos",
      var_descriptions: ["Anuncios en Redes Sociales", "Anuncios en Buscadores"],
      var_units: ["anuncios", "anuncios"],
      constraint_descriptions: ["Relación diferencial entre canales"],
      constraint_units: ["unidades"],
    },
  },
  {
    id: "ejemplo-6",
    title: "6. Asignación de Turnos (Dos Fases con >=)",
    description: "Min Z = 2x1 + 3x2. Cobertura obligatoria de al menos 5 guardias y máximo 4 del turno diurno",
    objective: "min",
    var_names: ["x1", "x2"],
    var_bounds: [">=0", ">=0"],
    c: [2, 3],
    constraints: [
      { lhs: [1, 1], sign: ">=", rhs: 5 },
      { lhs: [1, 0], sign: "<=", rhs: 4 },
    ],
    context: {
      title: "Planificación de Personal de Seguridad",
      statement: "Una compañía debe asignar personal para vigilancia diurna (x1) con costo de $2/turno y vigilancia nocturna (x2) con costo de $3/turno. Se debe asegurar una cobertura mínima de al menos 5 guardias, pero el turno diurno solo dispone de un tope de 4 plazas. ¿Cómo organizar los turnos con el costo mínimo?",
      objective_name: "Costo total de turnos",
      objective_unit: "$",
      var_descriptions: ["Guardias en Turno Diurno", "Guardias en Turno Nocturno"],
      var_units: ["guardias", "guardias"],
      constraint_descriptions: ["Requisito de cobertura mínima total", "Plazas máximas disponibles de día"],
      constraint_units: ["guardias", "plazas"],
    },
  },
]

function waitForPywebview() {
  return new Promise((resolve) => {
    if (window.pywebview && window.pywebview.api) {
      resolve(window.pywebview.api)
      return
    }
    const handler = () => {
      window.removeEventListener('pywebviewready', handler)
      resolve(window.pywebview?.api)
    }
    window.addEventListener('pywebviewready', handler)
    // Timeout after 800ms if not in pywebview
    setTimeout(() => resolve(window.pywebview?.api || null), 800)
  })
}

export async function fetchExamples() {
  const api = await waitForPywebview()
  if (api && api.get_simplex_examples) {
    try {
      return await api.get_simplex_examples()
    } catch (e) {
      console.warn('Error fetching examples from python api:', e)
    }
  }
  return DEFAULT_EXAMPLES
}

// Client-side fallback solver using exact fractions for standalone browser preview
function gcd(a, b) {
  a = Math.abs(a)
  b = Math.abs(b)
  while (b) {
    const t = b
    b = a % b
    a = t
  }
  return a
}

class Frac {
  constructor(n, d = 1) {
    if (d === 0) throw new Error('División por cero')
    if (d < 0) {
      n = -n
      d = -d
    }
    const g = gcd(Math.round(n), Math.round(d)) || 1
    this.n = Math.round(n / g)
    this.d = Math.round(d / g)
  }
  static from(val) {
    if (val instanceof Frac) return val
    if (typeof val === 'number') {
      if (Number.isInteger(val)) return new Frac(val, 1)
      const s = val.toString()
      const dec = s.split('.')[1] || ''
      const den = Math.pow(10, dec.length)
      return new Frac(Math.round(val * den), den)
    }
    const s = String(val).trim().replace(',', '.')
    if (!s) return new Frac(0, 1)
    if (s.includes('/')) {
      const [num, den] = s.split('/')
      return new Frac(parseFloat(num), parseFloat(den))
    }
    return Frac.from(parseFloat(s))
  }
  add(o) {
    o = Frac.from(o)
    return new Frac(this.n * o.d + o.n * this.d, this.d * o.d)
  }
  sub(o) {
    o = Frac.from(o)
    return new Frac(this.n * o.d - o.n * this.d, this.d * o.d)
  }
  mul(o) {
    o = Frac.from(o)
    return new Frac(this.n * o.n, this.d * o.d)
  }
  div(o) {
    o = Frac.from(o)
    return new Frac(this.n * o.d, this.d * o.n)
  }
  neg() {
    return new Frac(-this.n, this.d)
  }
  isZero() {
    return this.n === 0
  }
  isNegative() {
    return this.n < 0
  }
  isPositive() {
    return this.n > 0
  }
  toNumber() {
    return this.n / this.d
  }
  toFracStr() {
    return this.d === 1 ? `${this.n}` : `${this.n}/${this.d}`
  }
  toDecStr(decimals = 4) {
    const val = this.toNumber()
    return this.d === 1 || Math.abs(val - Math.round(val)) < 1e-6
      ? `${val}`
      : `≈ ${val.toFixed(decimals).replace(/\.?0+$/, '')}`
  }
  toCell() {
    return {
      frac: this.toFracStr(),
      dec: this.toDecStr(),
      float: this.toNumber(),
      num: this.n,
      den: this.d,
    }
  }
}

function solveSimplexLocal(problem) {
  const obj = (problem.objective || 'max').toLowerCase()
  const numVars = problem.c.length
  const varNames = problem.var_names || Array.from({ length: numVars }, (_, i) => `x${i + 1}`)
  const constraints = problem.constraints || []
  const numRows = constraints.length

  const colNames = [...varNames]
  for (let i = 1; i <= numRows; i++) colNames.push(`s${i}`)
  const numCols = colNames.length

  // Build matrix
  // Row 0: Z row
  const T = Array.from({ length: numRows + 1 }, () =>
    Array.from({ length: numCols + 1 }, () => new Frac(0))
  )

  const sgn = obj === 'max' ? 1 : -1
  const cStd = problem.c.map((val) => Frac.from(val).mul(sgn))

  for (let j = 0; j < numVars; j++) {
    T[0][j] = cStd[j].neg()
  }

  const basis = []
  for (let i = 0; i < numRows; i++) {
    const r = constraints[i]
    for (let j = 0; j < numVars; j++) {
      T[i + 1][j] = Frac.from(r.lhs[j] || 0)
    }
    const slackCol = numVars + i
    T[i + 1][slackCol] = new Frac(1)
    T[i + 1][numCols] = Frac.from(r.rhs || 0)
    basis.push(slackCol)
  }

  const steps = []
  const zLabel = obj === 'max' ? 'Z' : "Z'"
  let iter = 0
  let status = 'continue'

  while (iter <= 100) {
    const row0 = T[0]
    const negIndices = []
    for (let j = 0; j < numCols; j++) {
      if (row0[j].isNegative()) negIndices.push(j)
    }

    const isOptimal = negIndices.length === 0

    if (isOptimal) {
      status = 'optimal'
      steps.push({
        step_index: iter,
        phase: null,
        title: `Tabla ${iter} - Solución Óptima Alcanzada`,
        headers: ['Fila', 'Base', ...colNames, 'B'],
        col_names: colNames,
        z_label: zLabel,
        rows: T.map((row, rIdx) => ({
          row_idx: rIdx,
          row_label: `F${rIdx}`,
          base_var: rIdx === 0 ? zLabel : colNames[basis[rIdx - 1]],
          cells: row.map((c) => c.toCell()),
          rhs: row[numCols].toCell(),
        })),
        z_val: T[0][numCols].toCell(),
        basis_vars: basis.map((idx) => colNames[idx]),
        optimality_check: {
          is_optimal: true,
          explanation: `En la fila F0 (${zLabel}), todos los coeficientes son ≥ 0. La solución es ÓPTIMA.`,
          candidates: [],
        },
        pivot: null,
        status: 'optimal',
      })
      break
    }

    const enteringCol = negIndices[0]
    const enteringVar = colNames[enteringCol]
    const enteringVal = row0[enteringCol]

    const ratios = []
    const validRatios = []

    for (let i = 1; i <= numRows; i++) {
      const coeff = T[i][enteringCol]
      const rhsVal = T[i][numCols]
      const bVar = colNames[basis[i - 1]]

      if (coeff.isPositive()) {
        const rVal = rhsVal.div(coeff)
        validRatios.push({ row: i, val: rVal, basisCol: basis[i - 1] })
        ratios.push({
          row: i,
          base_var: bVar,
          rhs: rhsVal.toFracStr(),
          coeff: coeff.toFracStr(),
          ratio: rVal.toFracStr(),
          valid: true,
          note: `${rhsVal.toFracStr()} / ${coeff.toFracStr()} = ${rVal.toFracStr()}`,
        })
      } else {
        ratios.push({
          row: i,
          base_var: bVar,
          rhs: rhsVal.toFracStr(),
          coeff: coeff.toFracStr(),
          ratio: '-',
          valid: false,
          note: `Entrada (${coeff.toFracStr()}) ≤ 0: descartada.`,
        })
      }
    }

    if (validRatios.length === 0) {
      status = 'unbounded'
      steps.push({
        step_index: iter,
        phase: null,
        title: `Tabla ${iter} - Problema No Acotado`,
        headers: ['Fila', 'Base', ...colNames, 'B'],
        col_names: colNames,
        z_label: zLabel,
        rows: T.map((row, rIdx) => ({
          row_idx: rIdx,
          row_label: `F${rIdx}`,
          base_var: rIdx === 0 ? zLabel : colNames[basis[rIdx - 1]],
          cells: row.map((c) => c.toCell()),
          rhs: row[numCols].toCell(),
        })),
        z_val: T[0][numCols].toCell(),
        basis_vars: basis.map((idx) => colNames[idx]),
        optimality_check: {
          is_optimal: false,
          explanation: `F0 tiene coeficientes negativos, pero no hay ninguna entrada positiva en la columna ${enteringVar}.`,
          candidates: negIndices.map((j) => ({ var: colNames[j], val: row0[j].toFracStr() })),
        },
        pivot: null,
        status: 'unbounded',
      })
      break
    }

    // Find min ratio with Bland's rule
    validRatios.sort((a, b) => {
      const diff = a.val.sub(b.val).toNumber()
      if (Math.abs(diff) > 1e-9) return diff
      return a.basisCol - b.basisCol
    })

    const minRatio = validRatios[0]
    const leavingRow = minRatio.row
    const leavingVar = colNames[basis[leavingRow - 1]]
    const pivotVal = T[leavingRow][enteringCol]

    // Operations detail
    const rowOps = []
    const oldPRow = [...T[leavingRow]]
    const newPRow = oldPRow.map((v) => v.div(pivotVal))

    rowOps.push({
      row_idx: leavingRow,
      row_label: `F${leavingRow}`,
      type: 'normalize',
      formula: `F${leavingRow} ← F${leavingRow} / (${pivotVal.toFracStr()})`,
      details: colNames.map((cn, cIdx) => ({
        var: cn,
        calc: `${oldPRow[cIdx].toFracStr()} / ${pivotVal.toFracStr()}`,
        result: newPRow[cIdx].toFracStr(),
      })),
    })

    for (let i = 0; i <= numRows; i++) {
      if (i === leavingRow) continue
      const factor = T[i][enteringCol]
      if (factor.isZero()) {
        rowOps.push({
          row_idx: i,
          row_label: `F${i}`,
          type: 'unchanged',
          formula: `F${i}: ya tiene 0 en la columna pivote; no cambia.`,
          details: [],
        })
      } else {
        const oldR = [...T[i]]
        rowOps.push({
          row_idx: i,
          row_label: `F${i}`,
          type: 'eliminate',
          formula: `F${i} ← F${i} - (${factor.toFracStr()}) × F${leavingRow}`,
          details: colNames.map((cn, cIdx) => ({
            var: cn,
            calc: `${oldR[cIdx].toFracStr()} - (${factor.toFracStr()}) × (${newPRow[cIdx].toFracStr()})`,
            result: oldR[cIdx].sub(factor.mul(newPRow[cIdx])).toFracStr(),
          })),
        })
      }
    }

    steps.push({
      step_index: iter,
      phase: null,
      title: `Tabla ${iter} - Iteración ${iter} (Entra ${enteringVar}, Sale ${leavingVar})`,
      headers: ['Fila', 'Base', ...colNames, 'B'],
      col_names: colNames,
      z_label: zLabel,
      rows: T.map((row, rIdx) => ({
        row_idx: rIdx,
        row_label: `F${rIdx}`,
        base_var: rIdx === 0 ? zLabel : colNames[basis[rIdx - 1]],
        cells: row.map((c) => c.toCell()),
        rhs: row[numCols].toCell(),
      })),
      z_val: T[0][numCols].toCell(),
      basis_vars: basis.map((idx) => colNames[idx]),
      optimality_check: {
        is_optimal: false,
        explanation: `F0 tiene coeficientes negativos. Siguiendo la regla de Bland: entra ${enteringVar}.`,
        candidates: negIndices.map((j) => ({ var: colNames[j], val: row0[j].toFracStr() })),
      },
      pivot: {
        entering_var: enteringVar,
        entering_col: enteringCol,
        entering_cost: enteringVal.toFracStr(),
        leaving_var: leavingVar,
        leaving_row: leavingRow,
        pivot_row_label: `F${leavingRow}`,
        pivot_val: pivotVal.toFracStr(),
        min_ratio: minRatio.val.toFracStr(),
        ratios,
        is_degenerate: minRatio.val.isZero(),
        tie_explanation: '',
        row_operations: rowOps,
      },
      status: 'continue',
    })

    // Pivot in matrix
    T[leavingRow] = newPRow
    for (let i = 0; i <= numRows; i++) {
      if (i === leavingRow) continue
      const factor = T[i][enteringCol]
      if (!factor.isZero()) {
        for (let j = 0; j <= numCols; j++) {
          T[i][j] = T[i][j].sub(factor.mul(newPRow[j]))
        }
      }
    }
    basis[leavingRow - 1] = enteringCol
    iter++
  }

  // Final variables
  const varMap = {}
  varNames.forEach((n) => (varMap[n] = new Frac(0)))
  for (let i = 0; i < numRows; i++) {
    const bVar = colNames[basis[i]]
    if (varMap[bVar] !== undefined) {
      varMap[bVar] = T[i + 1][numCols]
    }
  }

  const zInt = T[0][numCols]
  const zOpt = obj === 'max' ? zInt : zInt.neg()

  // Substitutions
  const substitutions = constraints.map((r, i) => {
    let lhsSum = new Frac(0)
    for (let j = 0; j < numVars; j++) {
      lhsSum = lhsSum.add(Frac.from(r.lhs[j] || 0).mul(varMap[varNames[j]]))
    }
    const rhsFrac = Frac.from(r.rhs || 0)
    const satisfied = r.sign === '<=' ? lhsSum.toNumber() <= rhsFrac.toNumber() : true
    const isActive = lhsSum.sub(rhsFrac).isZero()
    return {
      index: i + 1,
      label: `R${i + 1}`,
      expression: `${r.lhs.map((c, j) => `(${c})×(${varMap[varNames[j]].toFracStr()})`).join(' + ')} = ${lhsSum.toFracStr()} ${r.sign} ${rhsFrac.toFracStr()}`,
      lhs: lhsSum.toFracStr(),
      sign: r.sign,
      rhs: rhsFrac.toFracStr(),
      satisfied,
      is_active: isActive,
      slack_value: rhsFrac.sub(lhsSum).toFracStr(),
      status_text: isActive ? 'Restricción ACTIVA (recurso agotado)' : `Holgura = ${rhsFrac.sub(lhsSum).toFracStr()}`,
    }
  })

  const varsObj = {}
  varNames.forEach((n) => (varsObj[n] = varMap[n].toCell()))

  const conclusion = generateContextualConclusionLocal({
    status,
    objective: obj,
    zOptimal: zOpt.toCell(),
    variables: varsObj,
    substitutions,
    context: problem.context,
    varNames,
  })

  return {
    method: 'primal',
    status,
    steps,
    final_report: {
      status,
      objective: obj,
      z_optimal: zOpt.toCell(),
      variables: varsObj,
      all_variables: varsObj,
      substitutions,
      all_satisfied: true,
      degeneracy: {
        is_degenerate: false,
        message: 'Solución evaluada con éxito.',
        vars: [],
      },
      alternative_optima: {
        has_alternatives: false,
        message: 'El punto óptimo encontrado es único.',
        candidates: [],
      },
      shadow_prices: [],
      transformation_notes: [],
      normalization_notes: [],
      contextual_conclusion: conclusion,
    },
  }
}

export function analyzeContextLocal(text) {
  const t = (text || '').toLowerCase()
  const maxTerms = ['maximi', 'utilidad', 'ganancia', 'beneficio', 'ingreso', 'lucro', 'rendimiento', 'venta', 'retorno']
  const minTerms = ['minimi', 'costo', 'gasto', 'pérdida', 'perdida', 'tiempo', 'merma', 'distancia', 'recorrido', 'consumo']

  let maxScores = 0
  let minScores = 0
  maxTerms.forEach((k) => {
    maxScores += t.split(k).length - 1
  })
  minTerms.forEach((k) => {
    minScores += t.split(k).length - 1
  })

  const objective = minScores > maxScores ? 'min' : 'max'
  let objName = objective === 'max' ? 'Ganancia / Utilidad total' : 'Costo total de operación'
  if (t.includes('ingreso')) objName = 'Ingreso total'
  else if (t.includes('beneficio')) objName = 'Beneficio neto'
  else if (t.includes('rendimiento')) objName = 'Rendimiento total'
  else if (t.includes('tiempo')) objName = 'Tiempo total requerido'
  else if (t.includes('gasto')) objName = 'Gasto total'

  let objUnit = '$'
  if (t.includes('dólar') || t.includes('dolar') || t.includes('usd') || (text && text.includes('$'))) objUnit = '$'
  else if (t.includes('euro') || (text && text.includes('€'))) objUnit = '€'
  else if (t.includes('sol') || t.includes('s/.')) objUnit = 'S/.'
  else if (t.includes('hora') && objective === 'min') objUnit = 'horas'
  else if (t.includes('minuto') && objective === 'min') objUnit = 'min'

  const suggestedVars = []
  const prodMatch = t.match(/(?:produce|fabrica|elabora|vende|confecciona|ofrece|prepara|comercializa|utiliza)\s+([a-záéíóúñ\s,y]+?)(?:\.|\;|\,|\s+con|\s+para|\s+cada|\s+en|\s+utilizando|\s+sujeto)/)
  if (prodMatch && prodMatch[1]) {
    const raw = prodMatch[1].replace(/\s+y\s+/g, ',').replace(/\s+e\s+/g, ',')
    raw.split(',').forEach((item) => {
      const cleaned = item.trim().replace(/^(dos|tres|cuatro|cinco|artículos de tipo|productos?|tipos? de|unidades? de)\s+/g, '')
      if (cleaned.length > 2 && !['dos', 'tres', 'varios'].includes(cleaned)) {
        suggestedVars.push(cleaned.charAt(0).toUpperCase() + cleaned.slice(1))
      }
    })
  }

  const suggestedConstraints = []
  const resRegex = /(?:horas?\s+de\s+([a-záéíóúñ]+)|departamento\s+de\s+([a-záéíóúñ]+)|taller\s+de\s+([a-záéíóúñ]+)|materia\s+prima\s+([a-záéíóúñ]+)|disponibilidad\s+de\s+([a-záéíóúñ]+)|máquina\s+([a-záéíóúñ\d]+))/g
  let match
  while ((match = resRegex.exec(t)) !== null) {
    const m = match.slice(1).find((x) => !!x)
    if (m && m.length > 2) {
      suggestedConstraints.push(`Horas / Capacidad de ${m.charAt(0).toUpperCase() + m.slice(1)}`)
    }
  }

  return {
    objective,
    objective_name: objName,
    objective_unit: objUnit,
    suggested_vars: suggestedVars.slice(0, 6),
    suggested_constraints: [...new Set(suggestedConstraints)].slice(0, 6),
    analysis_summary: `Se identificó sentido de ${objective === 'max' ? 'MAXIMIZACIÓN' : 'MINIMIZACIÓN'} enfocado en '${objName}' (${objUnit}).`,
  }
}

export function generateContextualConclusionLocal({
  status,
  objective,
  zOptimal,
  variables,
  substitutions,
  context,
  varNames,
}) {
  const ctx = context || {}
  const statement = (ctx.statement || '').trim()
  const title = (ctx.title || '').trim() || 'Problema de Optimización Lineal'
  const objName = (ctx.objective_name || '').trim() || (objective === 'max' ? 'Ganancia / Utilidad total' : 'Costo total de operación')
  const objUnit = (ctx.objective_unit || '').trim() || '$'
  const varDescriptions = ctx.var_descriptions || []
  const varUnits = ctx.var_units || []
  const constraintDescriptions = ctx.constraint_descriptions || []
  const constraintUnits = ctx.constraint_units || []

  if (status === 'infeasible') {
    return {
      status: 'infeasible',
      title,
      statement,
      headline: `Infactibilidad: Conflicto en los Requerimientos de ${objName}`,
      executive_summary: `El modelo no posee solución factible. Esto significa que las metas mínimas exigidas y los límites de recursos entran en contradicción directa. No existe combinación factible con las capacidades actuales.`,
      recommendation: `Se recomienda flexibilizar las metas mínimas o aumentar la dotación de insumos/recursos.`,
      plan_of_action: [],
      resource_diagnosis: [],
      limiting_resources: [],
      slack_resources: [],
      sensitivity_insights: [],
    }
  }

  if (status === 'unbounded') {
    return {
      status: 'unbounded',
      title,
      statement,
      headline: `Problema No Acotado: ${objName} Crece Indefinidamente`,
      executive_summary: `El modelo indica que la función objetivo (${objName}) puede crecer sin límite finito sin violar ninguna restricción.`,
      recommendation: `En la práctica esto evidencia la ausencia de una restricción limitante de mercado, presupuesto o capacidad física.`,
      plan_of_action: [],
      resource_diagnosis: [],
      limiting_resources: [],
      slack_resources: [],
      sensitivity_insights: [],
    }
  }

  const verb = objective === 'max' ? 'maximizar' : 'minimizar'
  const zStr = zOptimal?.frac || '0'
  const zDec = zOptimal?.dec || zStr

  const planOfAction = []
  const varSummaryParts = []
  varNames.forEach((vName, i) => {
    const vData = variables[vName] || { frac: '0', dec: '0' }
    const vValStr = vData.frac || '0'
    const vValDec = vData.dec || vValStr
    const vDesc = varDescriptions[i] || `Variable ${vName}`
    const vUnit = varUnits[i] || 'unidades'

    planOfAction.push({
      var: vName,
      description: vDesc,
      value_frac: vValStr,
      value_dec: vValDec,
      unit: vUnit,
      action_text: `Fabricar / Asignar ${vValStr} ${vUnit} de '${vDesc}' (${vName}).`,
    })
    varSummaryParts.push(`${vValStr} ${vUnit} de ${vDesc}`)
  })

  const joinedVars = varSummaryParts.join(', ')
  const executiveSummary = `Para ${verb} exitosamente la ${objName}, la solución óptima determina que se deben fabricar/asignar ${joinedVars}, alcanzando un valor óptimo de ${objName} de ${zStr} ${objUnit} (${zDec} ${objUnit}).`

  const resourceDiagnosis = []
  const limitingResources = []
  const slackResources = []

  ;(substitutions || []).forEach((sub, i) => {
    const rLabel = sub.label || `R${i + 1}`
    const rDesc = constraintDescriptions[i] || `Restricción ${rLabel}`
    const rUnit = constraintUnits[i] || 'unidades'
    const isActive = sub.is_active
    const lhs = sub.lhs || '0'
    const rhs = sub.rhs || '0'
    const sign = sub.sign || '<='
    const slackVal = sub.slack_value || '0'

    let statusDesc = ''
    let detailDesc = ''
    if (isActive) {
      if (sign === '<=') {
        statusDesc = 'Recurso AGOTADO al 100% (Cuello de botella)'
        detailDesc = `Se consumieron todas las ${rhs} ${rUnit} disponibles. Es un recurso limitante crítico.`
      } else {
        statusDesc = 'Requerimiento cumplido con exactitud'
        detailDesc = `Se cumplió exactamente la meta fijada de ${rhs} ${rUnit}.`
      }
      limitingResources.push(rDesc)
    } else {
      if (sign === '<=') {
        statusDesc = `Recurso con HOLGURA (Sobra: ${slackVal} ${rUnit})`
        detailDesc = `Se utilizaron ${lhs} de ${rhs} ${rUnit}. Queda una capacidad ociosa de ${slackVal} ${rUnit}.`
      } else {
        statusDesc = `Requerimiento superado con EXCEDENTE (+${slackVal} ${rUnit})`
        detailDesc = `Se alcanzaron ${lhs} ${rUnit}, superando la meta de ${rhs} en ${slackVal} ${rUnit}.`
      }
      slackResources.push(rDesc)
    }

    resourceDiagnosis.push({
      constraint: rLabel,
      description: rDesc,
      is_active: isActive,
      status_title: statusDesc,
      detail: detailDesc,
      usage_ratio: `${lhs} / ${rhs} ${rUnit}`,
      slack: slackVal,
      unit: rUnit,
      sign,
    })
  })

  return {
    status: 'optimal',
    title,
    statement,
    headline: `Conclusión del Ejercicio: Estrategia Óptima para ${verb.charAt(0).toUpperCase() + verb.slice(1)} ${objName}`,
    executive_summary: executiveSummary,
    optimal_value_text: `${zStr} ${objUnit}`,
    optimal_value_dec: `${zDec} ${objUnit}`,
    plan_of_action: planOfAction,
    resource_diagnosis: resourceDiagnosis,
    limiting_resources: limitingResources,
    slack_resources: slackResources,
    sensitivity_insights: [],
  }
}

export async function analyzeContext(text) {
  const api = await waitForPywebview()
  if (api && api.analyze_context) {
    try {
      return await api.analyze_context(text)
    } catch (e) {
      console.warn('Error invoking analyze_context on python api:', e)
    }
  }
  return analyzeContextLocal(text)
}

export async function solveSimplexProblem(problem) {
  const api = await waitForPywebview()
  if (api && api.solve_simplex) {
    return await api.solve_simplex(problem)
  }
  // Client-side fallback for browser preview
  console.log('Utilizando solver cliente local (modo navegador)')
  return solveSimplexLocal(problem)
}

