from dataclasses import dataclass


@dataclass(frozen=True)
class Sala:
    id: int
    nombre: str
    salidas: tuple  # de Salida, siempre en orden N, S, E, O