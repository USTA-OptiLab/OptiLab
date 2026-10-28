"""Métodos para obtener una solución básica factible inicial.

Todos reciben (costos, oferta, demanda, eps) de un problema balanceado y devuelven
(asignacion, basicas): la matriz de asignaciones y el conjunto de celdas básicas,
que siempre tiene m + n - 1 celdas (en caso degenerado se completa con celdas en 0).
"""

import numpy as np


def _completar_base(asignacion, costos, eps):
    """Celdas con asignación positiva + celdas en 0 (las más baratas) hasta formar un árbol."""
    m, n = asignacion.shape
    padre = list(range(m + n))

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    basicas = set()
    for i, j in np.argwhere(asignacion > eps):
        i, j = int(i), int(j)
        padre[raiz(i)] = raiz(m + j)
        basicas.add((i, j))

    candidatas = sorted(
        (costos[i, j], i, j) for i in range(m) for j in range(n) if (i, j) not in basicas
    )
    for _, i, j in candidatas:
        if len(basicas) == m + n - 1:
            break
        if raiz(i) != raiz(m + j):
            padre[raiz(i)] = raiz(m + j)
            basicas.add((i, j))
    return basicas


def esquina_noroeste(costos, oferta, demanda, eps=1e-9):
    m, n = costos.shape
    o, d = oferta.copy(), demanda.copy()
    x = np.zeros((m, n))
    i = j = 0
    while i < m and j < n:
        q = min(o[i], d[j])
        x[i, j] = q
        o[i] -= q
        d[j] -= q
        if o[i] <= eps:
            i += 1
        else:
            j += 1
    return x, _completar_base(x, costos, eps)


def costo_minimo(costos, oferta, demanda, eps=1e-9):
    m, n = costos.shape
    o, d = oferta.copy(), demanda.copy()
    x = np.zeros((m, n))
    for _, i, j in sorted((costos[i, j], i, j) for i in range(m) for j in range(n)):
        q = min(o[i], d[j])
        if q > eps:
            x[i, j] = q
            o[i] -= q
            d[j] -= q
    return x, _completar_base(x, costos, eps)


def vogel(costos, oferta, demanda, eps=1e-9):
    m, n = costos.shape
    o, d = oferta.copy(), demanda.copy()
    x = np.zeros((m, n))
    filas = set(range(m))
    cols = set(range(n))

    def penalizacion(valores):
        valores = sorted(valores)
        return valores[1] - valores[0] if len(valores) > 1 else 0.0

    while filas and cols:
        mejor = None  # (penalización, es_columna, índice)
        for i in sorted(filas):
            p = penalizacion([costos[i, j] for j in cols])
            if mejor is None or p > mejor[0]:
                mejor = (p, False, i)
        for j in sorted(cols):
            p = penalizacion([costos[i, j] for i in filas])
            if p > mejor[0]:
                mejor = (p, True, j)

        _, es_col, k = mejor
        if es_col:
            j = k
            i = min(sorted(filas), key=lambda r: costos[r, j])
        else:
            i = k
            j = min(sorted(cols), key=lambda c: costos[i, c])

        q = min(o[i], d[j])
        x[i, j] = q
        o[i] -= q
        d[j] -= q
        # Si se agotan fila y columna a la vez solo se retira la fila (caso degenerado).
        if o[i] <= eps:
            filas.discard(i)
        else:
            cols.discard(j)
    return x, _completar_base(x, costos, eps)


METODOS = {
    "noroeste": esquina_noroeste,
    "costo_minimo": costo_minimo,
    "vogel": vogel,
}
