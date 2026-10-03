from dataclasses import dataclass


@dataclass(frozen=True)
class ContenidoSala:
    sala: int
    enemigos: tuple  # de InstanciaEnemigo
    objetos: tuple   # ids de catálogo
    trampas: tuple   # de InstanciaTrampa