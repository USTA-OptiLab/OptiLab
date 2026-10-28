"""Formato de texto del procedimiento; lo comparten la CLI, la GUI y la exportación."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

NOMBRES_METODO = {
    "noroeste": "Esquina noroeste",
    "costo_minimo": "Costo mínimo",
    "vogel": "Aproximación de Vogel",
}


def _num(x, dec):
    if abs(x - round(x)) < 1e-9:
        return str(round(x))
    return f"{x:.{dec}f}"


def _op(x, dec):
    """Número como operando de una resta: los negativos van entre paréntesis."""
    return f"({_num(x, dec)})" if x < 0 else _num(x, dec)


def _tabla(encabezados, filas):
    cols = list(zip(encabezados, *filas))
    anchos = [max(len(c) for c in col) for col in cols]
    def linea(celdas):
        return "  ".join(
            c.ljust(a) if k == 0 else c.rjust(a) for k, (c, a) in enumerate(zip(celdas, anchos))
        )
    return "\n".join([linea(encabezados), "-" * (sum(anchos) + 2 * (len(anchos) - 1))] + [linea(f) for f in filas])


def _tabla_asignacion(x, costos, basicas, origenes, destinos, dec, oferta=None, demanda=None):
    """Cada celda: asignación (costo); '-' si la celda no es básica."""
    basicas = set(basicas)
    encabezados = [""] + list(destinos) + (["Oferta"] if oferta is not None else [])
    filas = []
    for i, nombre in enumerate(origenes):
        celdas = [
            f"{_num(x[i, j], dec) if (i, j) in basicas else '-'} ({_num(costos[i, j], dec)})"
            for j in range(len(destinos))
        ]
        filas.append([nombre] + celdas + ([_num(oferta[i], dec)] if oferta is not None else []))
    if demanda is not None:
        filas.append(["Demanda"] + [_num(d, dec) for d in demanda] + [""])
    return _tabla(encabezados, filas)


def _titulo(texto):
    return f"{'=' * 60}\n{texto}\n{'=' * 60}"


def _etiqueta_celda(r, i, j):
    return f"({r.problema.origenes[i]},{r.problema.destinos[j]})"


def _formula_costo(x, costos, dec):
    terminos = [
        f"{_num(x[i, j], dec)}×{_num(costos[i, j], dec)}"
        for i in range(x.shape[0]) for j in range(x.shape[1]) if x[i, j] > 1e-9
    ]
    return " + ".join(terminos) if terminos else "0"


def bloque_datos(r):
    p, o = r.problema, r.opciones
    dec = o.decimales
    texto = [_titulo("DATOS DEL PROBLEMA")]
    texto.append(f"Objetivo: {o.modo}")
    texto.append(_tabla(
        [""] + p.destinos + ["Oferta"],
        [[p.origenes[i]] + [_num(p.costos[i, j], dec) for j in range(p.n)] + [_num(p.oferta[i], dec)]
         for i in range(p.m)] + [["Demanda"] + [_num(d, dec) for d in p.demanda] + [""]],
    ))
    po = r.problema_original
    if p is not po:
        lado = "destino" if p.columna_ficticia is not None else "origen"
        texto.append(
            f"\nSuma de oferta ({_num(po.oferta.sum(), dec)}) ≠ suma de demanda "
            f"({_num(po.demanda.sum(), dec)}): se agrega un {lado} ficticio con costo 0."
        )
    if o.modo == "maximizar":
        texto.append("\nMaximización: se resuelve minimizando -c; las ecuaciones y los Δ usan -c.")
    return "\n".join(texto)


def bloque_inicial(r):
    p, o = r.problema, r.opciones
    dec = o.decimales
    texto = [_titulo(f"SOLUCIÓN INICIAL — {NOMBRES_METODO[o.metodo_inicial]}")]
    texto.append(_tabla_asignacion(r.asignacion_inicial, p.costos, r.basicas_inicial, p.origenes, p.destinos, dec))
    texto.append("(celda: asignación (costo); '-' = no básica)")
    texto.append(f"\nCeldas básicas: {len(r.basicas_inicial)} (m + n - 1 = {p.m + p.n - 1})")
    texto.append(f"Costo inicial = {_formula_costo(r.asignacion_inicial, p.costos, dec)} = {_num(r.costo_inicial, dec)}")
    return "\n".join(texto)


def bloque_iteracion(r, it):
    p, o = r.problema, r.opciones
    dec = o.decimales
    c = r.costos_trabajo
    texto = [_titulo(f"ITERACIÓN {it.numero}")]

    if o.mostrar_asignacion_por_iteracion:
        texto.append(_tabla_asignacion(it.asignacion, p.costos, it.basicas, p.origenes, p.destinos, dec))
        texto.append(f"Costo total = {_num(it.costo, dec)}\n")

    if o.mostrar_potenciales:
        texto.append("Potenciales (u_i + v_j = c_ij en celdas básicas, u_1 = 0):")
        for i, j in it.basicas:
            texto.append(f"  u_{i + 1} + v_{j + 1} = {_num(c[i, j], dec)}")
        texto.append("  " + ", ".join(f"u_{i + 1} = {_num(a, dec)}" for i, a in enumerate(it.u)))
        texto.append("  " + ", ".join(f"v_{j + 1} = {_num(a, dec)}" for j, a in enumerate(it.v)))
        texto.append("")

    if o.mostrar_costos_reducidos:
        texto.append("Costos reducidos (Δ_ij = c_ij - u_i - v_j en celdas no básicas):")
        for i in range(p.m):
            for j in range(p.n):
                if not np.isnan(it.delta[i, j]):
                    marca = "  <- negativo" if it.delta[i, j] < -o.epsilon else ""
                    texto.append(
                        f"  Δ_{i + 1}{j + 1} = {_num(c[i, j], dec)} - {_op(it.u[i], dec)} - "
                        f"{_op(it.v[j], dec)} = {_num(it.delta[i, j], dec)}{marca}"
                    )
        texto.append("")

    if it.entrante is None:
        texto.append("Todos los Δ_ij ≥ 0: la solución actual es óptima.")
    else:
        i, j = it.entrante
        texto.append(f"Entra la celda {_etiqueta_celda(r, i, j)} (Δ = {_num(it.delta[i, j], dec)}).")
        if o.mostrar_ciclo:
            texto.append(
                "Ciclo: " + " → ".join(
                    f"{_etiqueta_celda(r, a, b)}{'+' if s > 0 else '−'}" for a, b, s in it.ciclo
                )
            )
            texto.append(f"θ = mín de las celdas con − = {_num(it.theta, dec)}")
            texto.append(f"Sale la celda {_etiqueta_celda(r, *it.sale)}.")
    return "\n".join(texto)


def bloque_final(r):
    po, p, o = r.problema_original, r.problema, r.opciones
    dec = o.decimales
    x = r.asignacion[: po.m, : po.n]
    texto = [_titulo("RESULTADO FINAL" if r.optimo else "RESULTADO (NO CONVERGIÓ)")]
    if not r.optimo:
        texto.append(f"Se alcanzó el máximo de {o.max_iteraciones} iteraciones sin llegar al óptimo.\n")

    basicas = {(i, j) for i in range(po.m) for j in range(po.n) if x[i, j] > o.epsilon}
    texto.append(_tabla_asignacion(x, po.costos, basicas, po.origenes, po.destinos, dec, po.oferta, po.demanda))
    texto.append("(celda: asignación (costo); '-' = sin envío)\n")

    for i, j in sorted(basicas):
        texto.append(
            f"  {po.origenes[i]} → {po.destinos[j]}: {_num(x[i, j], dec)} × {_num(po.costos[i, j], dec)}"
            f" = {_num(x[i, j] * po.costos[i, j], dec)}"
        )
    etiqueta = "Ganancia total" if o.modo == "maximizar" else "Costo total"
    texto.append(f"\n{etiqueta} = {_num(r.costo, dec)}  (solución inicial: {_num(r.costo_inicial, dec)})")
    texto.append(f"Iteraciones de mejora: {sum(1 for it in r.historial if it.entrante is not None)}")

    if p.columna_ficticia is not None:
        for i in range(po.m):
            sobrante = r.asignacion[i, p.columna_ficticia]
            if sobrante > o.epsilon:
                texto.append(f"Nota: la oferta de {po.origenes[i]} no se usa por completo ({_num(sobrante, dec)} sin enviar).")
    if p.fila_ficticia is not None:
        for j in range(po.n):
            faltante = r.asignacion[p.fila_ficticia, j]
            if faltante > o.epsilon:
                texto.append(f"Nota: la demanda de {po.destinos[j]} no se cubre por completo ({_num(faltante, dec)} sin atender).")
    if r.optimos_alternativos:
        texto.append("Nota: hay algún Δ = 0 en celdas no básicas, por lo que existen soluciones óptimas alternativas.")
    return "\n".join(texto)


def secciones(r, completo=False):
    """Lista de bloques de texto según las opciones; `completo` ignora los interruptores de visibilidad."""
    o = r.opciones
    if completo:
        o = replace(
            o, mostrar_procedimiento=True, mostrar_inicial=True, mostrar_potenciales=True,
            mostrar_costos_reducidos=True, mostrar_ciclo=True, mostrar_asignacion_por_iteracion=True,
        )
        r = replace(r, opciones=o)
    if not o.mostrar_procedimiento:
        return [bloque_final(r)]
    bloques = [bloque_datos(r)]
    if o.mostrar_inicial:
        bloques.append(bloque_inicial(r))
    bloques.extend(bloque_iteracion(r, it) for it in r.historial)
    bloques.append(bloque_final(r))
    return bloques


def formatear(r, completo=False):
    return "\n\n".join(secciones(r, completo))


def a_dict(r):
    po = r.problema_original
    return {
        "problema": po.a_dict(),
        "modo": r.opciones.modo,
        "metodo_inicial": r.opciones.metodo_inicial,
        "costo_inicial": r.costo_inicial,
        "costo": r.costo,
        "optimo": r.optimo,
        "optimos_alternativos": r.optimos_alternativos,
        "asignacion": r.asignacion[: po.m, : po.n].tolist(),
        "iteraciones": [
            {
                "numero": it.numero,
                "costo": it.costo,
                "asignacion": it.asignacion.tolist(),
                "u": it.u.tolist(),
                "v": it.v.tolist(),
                "entrante": it.entrante,
                "ciclo": [list(c) for c in it.ciclo],
                "theta": it.theta,
                "sale": it.sale,
            }
            for it in r.historial
        ],
    }


def exportar(r, ruta):
    """Guarda el procedimiento completo: .json (estructurado) o cualquier otra extensión (texto)."""
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".json":
        ruta.write_text(json.dumps(a_dict(r), indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        ruta.write_text(formatear(r, completo=True) + "\n", encoding="utf-8")
