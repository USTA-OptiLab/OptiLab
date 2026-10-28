"""Graphical method module for two-variable linear programming problems."""

from .api import GraphicMethodApi
from .solver import solve_graphical

__all__ = ["GraphicMethodApi", "solve_graphical"]
