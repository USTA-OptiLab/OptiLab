"""Modelo de un problema de Programación Lineal."""

from fractions import Fraction

SENSES = ("max", "min")
CON_TYPES = ("<=", ">=", "=")
SIGNS = (">=0", "<=0", "libre")


class Problem:
    """sense: 'max' | 'min'; c: coeficientes de la función objetivo;
    cons: lista de (coeficientes, tipo, rhs); signs: '>=0' | '<=0' | 'libre' por variable.
    """

    def __init__(self, sense, c, cons, signs, names=None):
        if sense not in SENSES:
            raise ValueError("El sentido debe ser 'max' o 'min'.")
        self.sense = sense
        self.c = [Fraction(v) for v in c]
        self.n = len(self.c)
        if self.n == 0:
            raise ValueError("Se necesita al menos una variable.")
        if not cons:
            raise ValueError("Se necesita al menos una restricción.")
        self.cons = []
        for i, (a, t, b) in enumerate(cons, 1):
            if len(a) != self.n:
                raise ValueError(f"La restricción {i} debe tener {self.n} coeficientes.")
            if t not in CON_TYPES:
                raise ValueError(f"Tipo inválido en la restricción {i}: use <=, >= o =.")
            self.cons.append(([Fraction(v) for v in a], t, Fraction(b)))
        self.signs = list(signs)
        if len(self.signs) != self.n or any(s not in SIGNS for s in self.signs):
            raise ValueError("Cada variable necesita un signo: >=0, <=0 o libre.")
        self.names = names or [f"x{j + 1}" for j in range(self.n)]
