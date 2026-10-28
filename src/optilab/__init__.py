"""OptiLab: método MODI (distribución modificada) para el problema de transporte."""

__version__ = "0.1.0"

from .modi import ResultadoMODI, resolver, resolver_modi
from .opciones import Opciones
from .problema import ProblemaTransporte

__all__ = ["Opciones", "ProblemaTransporte", "ResultadoMODI", "resolver", "resolver_modi"]
