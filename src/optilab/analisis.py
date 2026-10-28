"""Análisis posteriores a la solución: sensibilidad de costos, comparación de métodos iniciales
y estados para la visualización."""

from collections import deque
from dataclasses import dataclass, replace

import numpy as np

from .modi import ResultadoMODI, resolver
from .opciones import METODOS_INICIALES, Opciones
from .problema import ProblemaTransporte

INF = float("inf")


@dataclass
class RangoCosto:
    origen: str
    destino: str
    basica: bool
    costo: float
    minimo: float  # -inf si no hay cota inferior
    maximo: float  # +inf si no hay cota superior


def _componente_raiz(m, n, basicas, sin_arista):
    """Nodos (filas 0..m-1, columnas m..m+n-1) alcanzables desde la fila 0 sin usar `sin_arista`."""
    ady = [[] for _ in range(m + n)]
    for i, j in basicas:
        if (i, j) != sin_arista:
            ady[i].append(m + j)
            ady[m + j].append(i)
    vistos = {0}
    cola = deque([0])
    while cola:
        a = cola.popleft()
        for b in ady[a]:
            if b not in vistos:
                vistos.add(b)
                cola.append(b)
    return vistos


def sensibilidad(r: ResultadoMODI) -> list[RangoCosto]:
    """Rango de cada costo original (con los demás fijos) en el que la base óptima sigue siendo óptima.

    - Celda no básica: el costo puede subir sin límite y bajar hasta su costo reducido Δ.
    - Celda básica: al variar su costo d, los potenciales de uno de los dos subárboles en que
      queda dividida la base cambian en ±d, y cada Δ de una celda no básica cambia en 0 o ±d;
      exigir Δ ≥ 0 en todas da la cota inferior y la superior.
    Las filas y columnas ficticias no se reportan.
    """
    if not r.optimo:
        raise ValueError("la sensibilidad solo se calcula sobre una solución óptima")
    p, po = r.problema, r.problema_original
    m, n = p.m, p.n
    it = r.historial[-1]
    basicas = set(it.basicas)
    delta = it.delta
    maximizar = r.opciones.modo == "maximizar"

    filas = []
    for i in range(po.m):
        for j in range(po.n):
            costo = float(po.costos[i, j])
            if (i, j) in basicas:
                alcanzables = _componente_raiz(m, n, basicas, (i, j))
                sigma = 1.0 if i in alcanzables else -1.0
                en_s_fila = [k not in alcanzables for k in range(m)]
                en_s_col = [m + l not in alcanzables for l in range(n)]
                dmin, dmax = -INF, INF
                for k in range(m):
                    for l in range(n):
                        if np.isnan(delta[k, l]):
                            continue
                        e = sigma * (en_s_fila[k] - en_s_col[l])
                        if e > 0:
                            dmin = max(dmin, -delta[k, l])
                        elif e < 0:
                            dmax = min(dmax, delta[k, l])
                # d es el cambio del costo de trabajo; al maximizar es el opuesto del cambio real
                lo, hi = (costo - dmax, costo - dmin) if maximizar else (costo + dmin, costo + dmax)
                filas.append(RangoCosto(po.origenes[i], po.destinos[j], True, costo, lo, hi))
            else:
                d = float(delta[i, j])
                lo, hi = (-INF, costo + d) if maximizar else (costo - d, INF)
                filas.append(RangoCosto(po.origenes[i], po.destinos[j], False, costo, lo, hi))
    return filas


@dataclass
class FilaComparacion:
    metodo: str
    costo_inicial: float
    iteraciones: int  # iteraciones de mejora (cambios de base)
    costo_final: float
    optimo: bool


def comparar_metodos(problema: ProblemaTransporte, opciones: Opciones | None = None) -> list[FilaComparacion]:
    """Resuelve el problema con cada solución inicial y resume el esfuerzo de MODI en cada caso."""
    opciones = opciones or Opciones()
    filas = []
    for metodo in METODOS_INICIALES:
        r = resolver(problema, replace(opciones, metodo_inicial=metodo))
        mejoras = sum(1 for it in r.historial if it.entrante is not None)
        filas.append(FilaComparacion(metodo, r.costo_inicial, mejoras, r.costo, r.optimo))
    return filas


def titulo_estado(r: ResultadoMODI, k: int) -> str:
    """Nombre de la k-ésima vista (0-based) del historial."""
    it = r.historial[k]
    if k == 0 and it.entrante is None:
        return "Solución inicial (ya es óptima)"
    if k == 0:
        return "Iteración 1 — solución inicial"
    if it.entrante is None:
        return f"Iteración {it.numero} — solución óptima"
    return f"Iteración {it.numero}"
