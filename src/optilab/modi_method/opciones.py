"""Configuración centralizada: la usan la GUI, la CLI y las llamadas por código."""

from dataclasses import dataclass

METODOS_INICIALES = ("noroeste", "costo_minimo", "vogel")
MODOS = ("minimizar", "maximizar")
CRITERIOS_ENTRADA = ("mas_negativo", "primero_negativo")


@dataclass
class Opciones:
    metodo_inicial: str = "vogel"
    modo: str = "minimizar"
    criterio_entrada: str = "mas_negativo"

    # Procedimiento: si `mostrar_procedimiento` es False solo se muestra el resultado final.
    mostrar_procedimiento: bool = True
    mostrar_inicial: bool = True
    mostrar_potenciales: bool = True
    mostrar_costos_reducidos: bool = True
    mostrar_ciclo: bool = True
    mostrar_asignacion_por_iteracion: bool = True
    mostrar_sensibilidad: bool = False
    paso_a_paso: bool = False

    max_iteraciones: int = 100
    decimales: int = 2
    epsilon: float = 1e-9
    exportar: str | None = None

    def __post_init__(self):
        if self.metodo_inicial not in METODOS_INICIALES:
            raise ValueError(f"metodo_inicial debe ser uno de {METODOS_INICIALES}")
        if self.modo not in MODOS:
            raise ValueError(f"modo debe ser uno de {MODOS}")
        if self.criterio_entrada not in CRITERIOS_ENTRADA:
            raise ValueError(f"criterio_entrada debe ser uno de {CRITERIOS_ENTRADA}")
        if self.max_iteraciones < 1:
            raise ValueError("max_iteraciones debe ser al menos 1")
        if self.decimales < 0:
            raise ValueError("decimales no puede ser negativo")
        if self.epsilon <= 0:
            raise ValueError("epsilon debe ser positivo")
