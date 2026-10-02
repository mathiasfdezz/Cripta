from dataclasses import dataclass


@dataclass(frozen=True)
class InstanciaEnemigo:
    instancia: str
    tipo: str
    vida: int | None = None  # None = empieza con la vida_max del catálogo