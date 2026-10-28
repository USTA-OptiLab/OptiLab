"""Interfaz de consola: python -m optilab.cli [archivo.json] [opciones]."""

import argparse
import sys

from . import reporte
from .analisis import comparar_metodos
from .modi import resolver
from .opciones import CRITERIOS_ENTRADA, METODOS_INICIALES, MODOS, Opciones
from .problema import ProblemaTransporte


def _leer_fila(prompt, cantidad):
    while True:
        try:
            valores = [float(t) for t in input(prompt).replace(",", " ").split()]
        except ValueError:
            print("  Solo se admiten números.")
            continue
        if len(valores) == cantidad:
            return valores
        print(f"  Se esperaban {cantidad} valores.")


def problema_interactivo():
    m = int(input("Cantidad de orígenes: "))
    n = int(input("Cantidad de destinos: "))
    costos = [_leer_fila(f"Costos del origen {i + 1} ({n} valores): ", n) for i in range(m)]
    oferta = _leer_fila(f"Oferta ({m} valores): ", m)
    demanda = _leer_fila(f"Demanda ({n} valores): ", n)
    return ProblemaTransporte(costos, oferta, demanda)


def crear_parser():
    p = argparse.ArgumentParser(prog="optilab.cli", description="Método MODI para el problema de transporte.")
    p.add_argument("archivo", nargs="?", help="problema en JSON (costos, oferta, demanda); si falta, se piden por consola")
    p.add_argument("--inicial", choices=METODOS_INICIALES, default="vogel", help="método de solución inicial")
    p.add_argument("--modo", choices=MODOS, default="minimizar")
    p.add_argument("--criterio", choices=CRITERIOS_ENTRADA, default="mas_negativo", help="regla de la celda entrante")
    p.add_argument("--sin-procedimiento", action="store_true", help="mostrar solo el resultado final")
    p.add_argument("--no-inicial", action="store_true", help="ocultar la solución inicial")
    p.add_argument("--no-potenciales", action="store_true", help="ocultar el cálculo de u y v")
    p.add_argument("--no-costos-reducidos", action="store_true", help="ocultar los Δ")
    p.add_argument("--no-ciclo", action="store_true", help="ocultar ciclo, θ y celda que sale")
    p.add_argument("--no-asignacion", action="store_true", help="ocultar la tabla de asignación de cada iteración")
    p.add_argument("--sensibilidad", action="store_true", help="agregar el análisis de sensibilidad de costos")
    p.add_argument("--comparar", action="store_true", help="comparar las tres soluciones iniciales")
    p.add_argument("--paso-a-paso", action="store_true", help="pausar tras cada bloque (Enter para continuar)")
    p.add_argument("--max", type=int, default=100, dest="max_iteraciones", help="máximo de iteraciones")
    p.add_argument("--decimales", type=int, default=2)
    p.add_argument("--exportar", metavar="RUTA", help="guardar el procedimiento completo (.txt o .json)")
    return p


def opciones_desde_args(a):
    return Opciones(
        metodo_inicial=a.inicial,
        modo=a.modo,
        criterio_entrada=a.criterio,
        mostrar_procedimiento=not a.sin_procedimiento,
        mostrar_inicial=not a.no_inicial,
        mostrar_potenciales=not a.no_potenciales,
        mostrar_costos_reducidos=not a.no_costos_reducidos,
        mostrar_ciclo=not a.no_ciclo,
        mostrar_asignacion_por_iteracion=not a.no_asignacion,
        mostrar_sensibilidad=a.sensibilidad,
        paso_a_paso=a.paso_a_paso,
        max_iteraciones=a.max_iteraciones,
        decimales=a.decimales,
        exportar=a.exportar,
    )


def main(argv=None):
    args = crear_parser().parse_args(argv)
    try:
        opciones = opciones_desde_args(args)
        problema = ProblemaTransporte.desde_json(args.archivo) if args.archivo else problema_interactivo()
        resultado = resolver(problema, opciones)
        comparacion = comparar_metodos(problema, opciones) if args.comparar else None
    except (ValueError, OSError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada cancelada.", file=sys.stderr)
        return 1

    bloques = reporte.secciones(resultado)
    for k, bloque in enumerate(bloques):
        print(bloque + "\n")
        if opciones.paso_a_paso and k < len(bloques) - 1:
            try:
                input("[Enter para continuar] ")
            except EOFError:
                opciones.paso_a_paso = False

    if comparacion:
        print(reporte.bloque_comparacion(comparacion, opciones.modo, opciones.decimales) + "\n")

    if opciones.exportar:
        reporte.exportar(resultado, opciones.exportar)
        print(f"Procedimiento guardado en {opciones.exportar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
