"""Método MODI (distribución modificada) para el problema de transporte."""

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from .inicial import METODOS
from .opciones import Opciones
from .problema import ProblemaTransporte


@dataclass
class Iteracion:
    """Estado al inicio de una iteración y movimiento que se hace a partir de él."""

    numero: int
    asignacion: np.ndarray
    basicas: list
    u: np.ndarray
    v: np.ndarray
    delta: np.ndarray  # costos reducidos; nan en celdas básicas
    costo: float
    entrante: tuple | None = None  # None: ya es óptimo
    ciclo: list = field(default_factory=list)  # [(i, j, +1 | -1)]
    theta: float | None = None
    sale: tuple | None = None


@dataclass
class ResultadoMODI:
    problema_original: ProblemaTransporte
    problema: ProblemaTransporte  # balanceado
    opciones: Opciones
    costos_trabajo: np.ndarray  # los que se minimizan (negados si modo = maximizar)
    asignacion_inicial: np.ndarray
    basicas_inicial: set
    costo_inicial: float
    historial: list
    asignacion: np.ndarray
    costo: float
    optimo: bool  # False si se agotó max_iteraciones
    optimos_alternativos: bool


def calcular_potenciales(costos, basicas):
    """Resuelve u_i + v_j = c_ij sobre las celdas básicas (con u_0 = 0)."""
    m, n = costos.shape
    por_fila = [[] for _ in range(m)]
    por_col = [[] for _ in range(n)]
    for i, j in basicas:
        por_fila[i].append(j)
        por_col[j].append(i)

    u = np.full(m, np.nan)
    v = np.full(n, np.nan)
    u[0] = 0.0
    cola = deque([(0, False)])  # (índice, es_columna)
    while cola:
        k, es_col = cola.popleft()
        if es_col:
            for i in por_col[k]:
                if np.isnan(u[i]):
                    u[i] = costos[i, k] - v[k]
                    cola.append((i, False))
        else:
            for j in por_fila[k]:
                if np.isnan(v[j]):
                    v[j] = costos[k, j] - u[k]
                    cola.append((j, True))
    if np.isnan(u).any() or np.isnan(v).any():
        raise RuntimeError(
            "la base no es conexa: no se pueden calcular los potenciales"
        )
    return u, v


def encontrar_ciclo(entrante, basicas, m, n):
    """Ciclo cerrado [(i, j, signo)] formado por la celda entrante y celdas básicas."""
    ie, je = entrante
    ady = [[] for _ in range(m + n)]  # nodos: filas 0..m-1, columnas m..m+n-1
    for i, j in basicas:
        ady[i].append(m + j)
        ady[m + j].append(i)

    padre = {ie: None}
    cola = deque([ie])
    while cola and (m + je) not in padre:
        a = cola.popleft()
        for b in ady[a]:
            if b not in padre:
                padre[b] = a
                cola.append(b)
    if (m + je) not in padre:
        raise RuntimeError(
            "no existe ciclo: la base no es un árbol que conecte la celda entrante"
        )

    # Camino desde la columna de la celda entrante hasta su fila: tiene cantidad impar de aristas,
    # así que los signos alternan -, +, ..., - y con la entrante (+) el ciclo queda balanceado.
    ciclo = [(ie, je, +1)]
    signo = -1
    b = m + je
    while padre[b] is not None:
        a = padre[b]
        i, j = (a, b - m) if b >= m else (b, a - m)
        ciclo.append((i, j, signo))
        signo = -signo
        b = a
    return ciclo


def _costos_reducidos(costos, basicas, u, v):
    delta = costos - u[:, None] - v[None, :]
    for i, j in basicas:
        delta[i, j] = np.nan
    return delta


def _elegir_entrante(delta, criterio, eps):
    negativos = np.where(np.isnan(delta), np.inf, delta) < -eps
    if not negativos.any():
        return None
    if criterio == "primero_negativo":
        i, j = np.argwhere(negativos)[0]
    else:
        i, j = np.unravel_index(
            np.argmin(np.where(negativos, delta, np.inf)), delta.shape
        )
    return int(i), int(j)


def resolver_modi(
    problema, asignacion_inicial, basicas_inicial, opciones=None, problema_original=None
):
    """Optimiza desde una solución básica factible. `problema` debe estar balanceado."""
    opciones = opciones or Opciones()
    eps = opciones.epsilon
    m, n = problema.m, problema.n
    signo_modo = -1.0 if opciones.modo == "maximizar" else 1.0
    c = signo_modo * problema.costos

    x = asignacion_inicial.copy()
    basicas = set(basicas_inicial)
    historial = []
    optimo = False

    for numero in range(1, opciones.max_iteraciones + 1):
        u, v = calcular_potenciales(c, basicas)
        delta = _costos_reducidos(c, basicas, u, v)
        it = Iteracion(
            numero,
            x.copy(),
            sorted(basicas),
            u,
            v,
            delta,
            float((problema.costos * x).sum()),
        )
        historial.append(it)

        entrante = _elegir_entrante(delta, opciones.criterio_entrada, eps)
        if entrante is None:
            optimo = True
            break

        ciclo = encontrar_ciclo(entrante, basicas, m, n)
        negativas = [(i, j) for i, j, s in ciclo if s < 0]
        theta = min(x[i, j] for i, j in negativas)
        sale = next((i, j) for i, j in negativas if x[i, j] <= theta + eps)
        for i, j, s in ciclo:
            x[i, j] += s * theta
        x[sale] = 0.0
        x[np.abs(x) <= eps] = 0.0
        basicas.add(entrante)
        basicas.discard(sale)
        it.entrante, it.ciclo, it.theta, it.sale = entrante, ciclo, float(theta), sale

    alternativos = optimo and bool(
        (np.abs(historial[-1].delta[~np.isnan(historial[-1].delta)]) <= eps).any()
    )
    return ResultadoMODI(
        problema_original=problema_original or problema,
        problema=problema,
        opciones=opciones,
        costos_trabajo=c,
        asignacion_inicial=asignacion_inicial.copy(),
        basicas_inicial=set(basicas_inicial),
        costo_inicial=float((problema.costos * asignacion_inicial).sum()),
        historial=historial,
        asignacion=x,
        costo=float((problema.costos * x).sum()),
        optimo=optimo,
        optimos_alternativos=alternativos,
    )


def resolver(problema, opciones=None):
    """Balancea, obtiene la solución inicial según `opciones` y aplica MODI."""
    opciones = opciones or Opciones()
    balanceado = problema.balancear()
    c = (-1.0 if opciones.modo == "maximizar" else 1.0) * balanceado.costos
    x0, basicas0 = METODOS[opciones.metodo_inicial](
        c, balanceado.oferta, balanceado.demanda, opciones.epsilon
    )
    return resolver_modi(balanceado, x0, basicas0, opciones, problema_original=problema)
