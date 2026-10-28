import sympy as sp
import pandas as pd
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

M = sp.Symbol("M")
VALOR_GRANDE = 10**6   # Para decidir el pivote, M se reemplaza por un número muy grande


# ---------------- Funciones de apoyo ----------------
def leerExpresion(texto):
    """Convierte '1,5x1 + 3x2' en una expresión de sympy con números exactos (1,5 -> 3/2)."""
    texto = texto.replace(",", ".")
    transformaciones = standard_transformations + (implicit_multiplication,)
    return sp.nsimplify(parse_expr(texto, transformations=transformaciones), rational=True)


def numero(valor):
    """Número con coma decimal y sin ceros sobrantes: 1.5 -> '1,5', 10.0 -> '10'."""
    valor = float(valor)
    if abs(valor) < 1e-9:
        return "0"
    return f"{valor:.4f}".rstrip("0").rstrip(".").replace(".", ",")


def formatear(valor):
    """Muestra un valor como en clase: M-1,5 / 40M+15 / 115."""
    valor = sp.expand(valor)
    coeficienteM, constante = valor.coeff(M), valor.subs(M, 0)
    if coeficienteM == 0:
        return numero(constante)
    textoM = "M" if coeficienteM == 1 else "-M" if coeficienteM == -1 else numero(coeficienteM) + "M"
    if constante == 0:
        return textoM
    return textoM + ("+" if constante > 0 else "-") + numero(abs(constante))


def valorNumerico(valor):
    """Valor aproximado reemplazando M por un número muy grande (solo para comparar)."""
    return float(sp.expand(valor).subs(M, VALOR_GRANDE))


def escribirEcuacion(fila, columnas):
    """{'x1': 2, 'x2': 1, 'S1': 1} -> '2x1 + x2 + S1'"""
    texto = ""
    for nombre in columnas:
        coeficiente = fila.get(nombre, 0)
        if coeficiente == 0:
            continue
        magnitud = "" if abs(coeficiente) == 1 else numero(abs(coeficiente))
        texto += f" {'-' if coeficiente < 0 else '+'} {magnitud}{nombre}"
    return texto.lstrip(" +")


def mostrarTabla(titulo, tabla, columnas, base):
    datos = [[formatear(valor) for valor in fila] for fila in tabla]
    tablaPandas = pd.DataFrame(datos, columns=columnas + ["K"], index=["Z"] + base)
    tablaPandas.index.name = "VB"
    print(f"\n--- {titulo} ---")
    print(tablaPandas.to_string())


# ---------------- Método de la Gran M ----------------
def granM(funcionTexto, tipo, restricciones):
    """
    funcionTexto : "1.5x1 + 2.5x2"
    tipo         : "min" o "max"
    restricciones: lista de (expresion, signo, rhs)
                   ej. [("2x1 + x2", "<=", 90), ("x1 + x2", ">=", 50)]
    """
    funcionZ = leerExpresion(funcionTexto)
    expresionesRestricciones = [leerExpresion(expresion) for expresion, _, _ in restricciones]

    # Variables x1, x2, ... encontradas en todo el modelo, en orden
    todasLasVariables = funcionZ.free_symbols.union(*[e.free_symbols for e in expresionesRestricciones])
    variables = sorted(todasLasVariables, key=lambda v: int(v.name[1:]))
    sinVariables = {v: 0 for v in variables}

    # 1. Transformar restricciones (holgura, exceso y artificial)
    print("\n--- RESTRICCIONES TRANSFORMADAS ---")
    holguras, artificiales, base, filasRestricciones = [], [], [], []
    for i, (expresion, (_, signo, rhs)) in enumerate(zip(expresionesRestricciones, restricciones), 1):
        fila = {v.name: expresion.coeff(v) for v in variables}
        if signo == "<=":
            fila[f"S{i}"] = 1
            holguras.append(f"S{i}")
            base.append(f"S{i}")
        elif signo == ">=":
            fila[f"S{i}"] = -1
            holguras.append(f"S{i}")
        if signo in (">=", "="):
            artificial = f"A{len(artificiales) + 1}"
            fila[artificial] = 1
            artificiales.append(artificial)
            base.append(artificial)
        # Si la expresión trae una constante, pasa restando al lado derecho
        fila["K"] = leerExpresion(str(rhs)) - expresion.subs(sinVariables)
        filasRestricciones.append(fila)

    columnas = [v.name for v in variables] + holguras + artificiales
    for i, fila in enumerate(filasRestricciones, 1):
        print(f"R{i}: {escribirEcuacion(fila, columnas)} = {numero(fila['K'])}")

    # 2. Penalizar artificiales: MIN -> +M, MAX -> -M
    signoM = "+" if tipo == "min" else "-"
    print(f"\nZ = {funcionTexto}" + "".join(f" {signoM} M{a}" for a in artificiales))

    # 3. Tabla inicial (fila Z escrita como ecuación: Z - c·x ∓ M·A = 0)
    penalizacion = -M if tipo == "min" else M
    filaZ = ([-funcionZ.coeff(v) for v in variables] + [0] * len(holguras)
             + [penalizacion] * len(artificiales) + [0])
    tabla = [filaZ] + [[fila.get(c, 0) for c in columnas] + [fila["K"]] for fila in filasRestricciones]
    tabla = [[sp.sympify(valor) for valor in fila] for fila in tabla]
    mostrarTabla("TABLA INICIAL", tabla, columnas, base)

    # 4. Eliminar de Z las artificiales que están en la base
    for i, nombre in enumerate(base, 1):
        if nombre in artificiales:
            factor = -tabla[0][columnas.index(nombre)]
            tabla[0] = [sp.expand(z + factor * r) for z, r in zip(tabla[0], tabla[i])]

    # 5. Iterar (sin imprimir) hasta cumplir el criterio de optimalidad
    for _ in range(50):
        valoresZ = [valorNumerico(v) for v in tabla[0][:-1]]
        if tipo == "min":
            columnaPivote = valoresZ.index(max(valoresZ))     # más positivo
            esOptimo = valoresZ[columnaPivote] <= 1e-9
        else:
            columnaPivote = valoresZ.index(min(valoresZ))     # más negativo
            esOptimo = valoresZ[columnaPivote] >= -1e-9
        if esOptimo:
            break

        # Razón mínima: K / coeficiente positivo
        razones = [(tabla[i][-1] / tabla[i][columnaPivote], i)
                   for i in range(1, len(tabla)) if tabla[i][columnaPivote] > 0]
        if not razones:
            print("\nLa solución es NO ACOTADA.")
            return None
        _, filaPivote = min(razones)

        # Pivoteo: pivote en 1 y ceros en el resto de la columna
        pivote = tabla[filaPivote][columnaPivote]
        tabla[filaPivote] = [v / pivote for v in tabla[filaPivote]]
        for i in range(len(tabla)):
            if i != filaPivote:
                factor = -tabla[i][columnaPivote]          # inverso aditivo
                tabla[i] = [sp.expand(v + factor * p) for v, p in zip(tabla[i], tabla[filaPivote])]
        base[filaPivote - 1] = columnas[columnaPivote]

    mostrarTabla("TABLA FINAL", tabla, columnas, base)

    # 6. Leer la solución: básicas = K, no básicas = 0
    valores = {nombre: 0 for nombre in columnas}
    for i, nombre in enumerate(base, 1):
        valores[nombre] = tabla[i][-1]

    if any(valores[a] > 0 for a in artificiales) or tabla[0][-1].has(M):
        print("\nEl problema es NO FACTIBLE: una artificial quedó positiva.")
        return None

    valorZ = tabla[0][-1] + funcionZ.subs(sinVariables)   # se suma la constante de Z, si hay
    textoVariables = ", ".join(f"{v.name} = {numero(valores[v.name])}" for v in variables)
    mensaje = (f"La optimalidad para {'minimizar' if tipo == 'min' else 'maximizar'} "
               f"es Z = {numero(valorZ)}, ingresando {textoVariables}.")
    print(f"\n{mensaje}")

    return {
        "valorZ": float(valorZ),
        "variables": {v.name: float(valores[v.name]) for v in variables},
        "mensaje": mensaje,
    }


# ---------------- Captura de datos (código del grupo) ----------------
def MetodoGranM():
    print("--- MÉTODO DE LA GRAN M ---")
    funcionTexto = input("Función objetivo (ej: 1.5x1 + 2.5x2): ")
    tipo = input("¿Es max o min?: ").strip().lower()[:3]

    cantidadRestricciones = int(input("¿Cuántas restricciones?: "))
    restricciones = []
    for i in range(1, cantidadRestricciones + 1):
        print(f"\nRestricción {i}:")
        expresion = input("  Expresión (ej: x1 + 2x2): ")
        signo = input("  Signo (<=, >=, =): ").strip().replace("≤", "<=").replace("≥", ">=")
        rhs = input("  Lado derecho (RHS): ")
        restricciones.append((expresion, signo, rhs))

    return granM(funcionTexto, tipo, restricciones)


if __name__ == "__main__":
    MetodoGranM()

"""
Muestra: modelo transformado, tabla inicial y tabla final con la solución.
El pivoteo se hace internamente, sin imprimir el procedimiento.

Uso desde otro archivo:
    from granM import MetodoGranM
    resultado = MetodoGranM()
"""