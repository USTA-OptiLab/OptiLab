"""
Método de Aproximación de Vogel (MAV) para el problema de transporte.

- Balancea automáticamente el problema (agrega origen o destino ficticio).
- Muestra las penalizaciones y la asignación de cada iteración.
- Entrega la solución básica factible inicial y el costo total.
"""

import math


def balance(costs, supply, demand):
    """Add a dummy row or column (cost 0) if supply != demand."""
    costs = [row[:] for row in costs]
    supply, demand = supply[:], demand[:]
    total_supply, total_demand = sum(supply), sum(demand)

    if total_supply > total_demand:
        for row in costs:
            row.append(0)
        demand.append(total_supply - total_demand)
        print(
            f"\n* Problema desbalanceado: se agrega un DESTINO ficticio con demanda {total_supply - total_demand}"
        )
    elif total_demand > total_supply:
        costs.append([0] * len(demand))
        supply.append(total_demand - total_supply)
        print(
            f"\n* Problema desbalanceado: se agrega un ORIGEN ficticio con oferta {total_demand - total_supply}"
        )
    else:
        print("\n* El problema está balanceado.")

    return costs, supply, demand


def penalty(values):
    """Difference between the two smallest costs."""
    if len(values) >= 2:
        a, b = sorted(values)[:2]
        return b - a
    return values[0] if values else 0


def print_table(
    costs,
    allocation,
    supply,
    demand,
    active_rows,
    active_cols,
    row_pen=None,
    col_pen=None,
):
    m, n = len(costs), len(costs[0])
    width = 11
    header = " " * 6 + "".join(f"{'D' + str(j + 1):^{width}}" for j in range(n))
    header += f"{'Oferta':^{width}}" + (f"{'Pen.':^7}" if row_pen else "")
    print(header)
    print("-" * len(header))

    for i in range(m):
        line = f"{'O' + str(i + 1):<6}"
        for j in range(n):
            cell = f"{costs[i][j]}"
            if allocation[i][j] is not None:
                cell += f"[{allocation[i][j]}]"
            line += f"{cell:^{width}}"
        crossed = "" if i in active_rows else " X"
        line += f"{str(supply[i]) + crossed:^{width}}"
        if row_pen:
            line += f"{row_pen.get(i, '-')!s:^7}"
        print(line)

    print("-" * len(header))
    line = f"{'Dem.':<6}" + "".join(
        f"{str(demand[j]) + ('' if j in active_cols else ' X'):^{width}}"
        for j in range(n)
    )
    print(line)
    if col_pen:
        print(
            f"{'Pen.':<6}"
            + "".join(f"{col_pen.get(j, '-')!s:^{width}}" for j in range(n))
        )


def solve_vogel(costs, supply, demand, show_steps=True):
    costs, supply, demand = balance(costs, supply, demand)
    m, n = len(costs), len(costs[0])
    remaining_supply, remaining_demand = supply[:], demand[:]
    allocation = [[None] * n for _ in range(m)]
    active_rows, active_cols = set(range(m)), set(range(n))
    iteration = 0

    def assign(i, j):
        quantity = min(remaining_supply[i], remaining_demand[j])
        allocation[i][j] = quantity
        remaining_supply[i] -= quantity
        remaining_demand[j] -= quantity
        return quantity

    while len(active_rows) > 1 and len(active_cols) > 1:
        iteration += 1

        # 1. Penalties per row and per column
        row_pen = {i: penalty([costs[i][j] for j in active_cols]) for i in active_rows}
        col_pen = {j: penalty([costs[i][j] for i in active_rows]) for j in active_cols}

        if show_steps:
            print(f"\n================ ITERACIÓN {iteration} ================")
            print_table(
                costs,
                allocation,
                remaining_supply,
                remaining_demand,
                active_rows,
                active_cols,
                row_pen,
                col_pen,
            )

        # 2. Highest penalty (tie-break: lowest cost, then largest assignable quantity)
        candidates = []
        for i, p in row_pen.items():
            j = min(active_cols, key=lambda c: costs[i][c])
            candidates.append(
                (
                    p,
                    -costs[i][j],
                    min(remaining_supply[i], remaining_demand[j]),
                    "row",
                    i,
                    j,
                )
            )
        for j, p in col_pen.items():
            i = min(active_rows, key=lambda r: costs[r][j])
            candidates.append(
                (
                    p,
                    -costs[i][j],
                    min(remaining_supply[i], remaining_demand[j]),
                    "column",
                    i,
                    j,
                )
            )

        p, _, _, kind, i, j = max(candidates, key=lambda c: (c[0], c[1], c[2]))

        # 3. Assign in the lowest-cost cell of that row/column
        quantity = assign(i, j)
        if show_steps:
            idx = i + 1 if kind == "row" else j + 1
            label = "fila" if kind == "row" else "columna"
            print(
                f"\n-> Mayor penalización: {p} ({label} {'O' if kind == 'row' else 'D'}{idx})"
            )
            print(
                f"-> Se asignan {quantity} unidades a la celda (O{i + 1}, D{j + 1}) con costo {costs[i][j]}"
            )

        # 4. Cross out a row or column (only one if both hit zero -> degeneracy)
        if remaining_supply[i] == 0 and remaining_demand[j] == 0:
            active_rows.discard(i)
            if show_steps:
                print(
                    f"-> Oferta y demanda en cero a la vez (degeneración): se tacha solo la fila O{i + 1}"
                )
        elif remaining_supply[i] == 0:
            active_rows.discard(i)
        else:
            active_cols.discard(j)

    # 5. A single row or column is left: assign everything that remains
    if active_rows and active_cols:
        if show_steps:
            print(
                "\n========= ÚLTIMA ETAPA: asignación directa de lo restante ========="
            )
        for i in sorted(active_rows):
            for j in sorted(active_cols, key=lambda c: costs[i][c]):
                if allocation[i][j] is None:
                    quantity = assign(i, j)
                    if show_steps:
                        print(
                            f"-> Se asignan {quantity} unidades a (O{i + 1}, D{j + 1}) con costo {costs[i][j]}"
                        )

    total_cost = sum(
        costs[i][j] * allocation[i][j]
        for i in range(m)
        for j in range(n)
        if allocation[i][j]
    )

    return costs, supply, demand, allocation, total_cost


def print_result(costs, supply, demand, allocation, total_cost):
    m, n = len(costs), len(costs[0])
    print("\n================ SOLUCIÓN INICIAL (VOGEL) ================")
    print("Formato de celda: costo[cantidad asignada]\n")
    print_table(costs, allocation, supply, demand, set(range(m)), set(range(n)))

    print("\nAsignaciones:")
    terms = []
    for i in range(m):
        for j in range(n):
            if allocation[i][j] is not None:
                print(
                    f"  X{i + 1}{j + 1} = {allocation[i][j]:>5}   (costo unitario {costs[i][j]})"
                )
                if allocation[i][j]:
                    terms.append(f"{costs[i][j]}*{allocation[i][j]}")

    basic = sum(1 for row in allocation for x in row if x is not None)
    print(f"\nVariables básicas: {basic}  (m + n - 1 = {m + n - 1})")
    if basic < m + n - 1:
        print("  Aviso: la solución es degenerada.")
    print(f"\nCosto total Z = {' + '.join(terms)}")
    print(f"Costo total Z = {total_cost}")


DEFAULT_CONTEXT = "Problema de transporte sin descripción."
EXAMPLE_CONTEXT = (
    "Una empresa tiene 3 fábricas y debe distribuir productos a 4 almacenes, "
    "buscando minimizar los costos de transporte."
)


def parse_number(text):
    """Return a finite, non-negative number (int when possible) or raise ValueError."""
    value = float(text)
    if not math.isfinite(value) or value < 0:
        raise ValueError
    return int(value) if value.is_integer() else value


def ask_context():
    print("\nDescriba brevemente el problema (puede dejarlo vacío).")
    print(
        "Ej: Una empresa tiene 3 fábricas y debe distribuir productos a 3 almacenes,"
        " buscando minimizar los costos de transporte."
    )
    return input("Problema: ").strip() or DEFAULT_CONTEXT


def ask_int(prompt, minimum=1):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("  Valor inválido: ingrese un número entero.")
            continue
        if value < minimum:
            print(f"  El valor debe ser mayor o igual a {minimum}.")
            continue
        return value


def ask_numbers(prompt, length):
    while True:
        try:
            values = [parse_number(x) for x in input(prompt).replace(",", " ").split()]
        except ValueError:
            print("  Valor inválido: use solo números finitos mayores o iguales a 0.")
            continue
        if len(values) != length:
            print(f"  Debe ingresar {length} valores y ingresó {len(values)}.")
            continue
        return values


def read_input():
    context = ask_context()
    m = ask_int("\nNúmero de orígenes (filas): ")
    n = ask_int("Número de destinos (columnas): ")
    print("\nIngrese la matriz de costos, una fila por línea, separada por espacios:")
    costs = [ask_numbers(f"  O{i + 1}: ", n) for i in range(m)]
    supply = ask_numbers(f"\nOferta de los {m} orígenes: ", m)
    demand = ask_numbers(f"Demanda de los {n} destinos: ", n)
    return context, costs, supply, demand


def print_interpretation(context, m, n, costs, allocation, total_cost):
    """Fixed-template reading of the result; only sizes and numbers change."""
    print("\n================ INTERPRETACIÓN ================")
    print(f"Problema: {context}")
    print(
        f"\nCon {m} orígenes y {n} destinos, la mejor distribución inicial"
        " encontrada es:"
    )
    for i in range(m):
        for j in range(n):
            if allocation[i][j]:
                print(
                    f"  - El origen O{i + 1} envía {allocation[i][j]} unidades al destino D{j + 1}"
                )

    if len(allocation[0]) > n:
        unsent = sum(allocation[i][n] or 0 for i in range(m))
        if unsent:
            print(
                f"\nSobra oferta: {unsent} unidades quedan sin enviar (destino ficticio)."
            )
    if len(allocation) > m:
        unmet = sum(x or 0 for x in allocation[m])
        if unmet:
            print(
                f"\nFalta oferta: {unmet} unidades de demanda no se cubren (origen ficticio)."
            )

    print(f"\nEl costo total de transporte de esta solución inicial es {total_cost}.")
    print("Nota: es una solución inicial factible; no necesariamente es la óptima.")


def main():
    print("MÉTODO DE APROXIMACIÓN DE VOGEL")
    print("1. Usar ejemplo")
    print("2. Ingresar datos propios")
    try:
        option = input("Opción: ").strip()

        if option == "2":
            context, costs, supply, demand = read_input()
        else:
            context = EXAMPLE_CONTEXT
            costs = [
                [19, 30, 50, 10],
                [70, 30, 40, 60],
                [40, 8, 70, 20],
            ]
            supply = [7, 9, 18]
            demand = [5, 8, 7, 14]
    except (EOFError, KeyboardInterrupt):
        print("\n\nEntrada cancelada. Fin del programa.")
        return

    print(f"\nProblema: {context}")
    result = solve_vogel(costs, supply, demand)
    print_result(*result)
    print_interpretation(
        context, len(costs), len(costs[0]), result[0], result[3], result[4]
    )


if __name__ == "__main__":
    main()
