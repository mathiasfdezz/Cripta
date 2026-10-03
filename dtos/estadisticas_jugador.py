from dataclasses import dataclass


@dataclass(frozen=True)
class EstadisticasJugador:
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int