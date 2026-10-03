from dataclasses import dataclass


@dataclass(frozen=True)
class ResumenCripta:
    id: str
    nombre: str
    salas: int
    dificultad: int