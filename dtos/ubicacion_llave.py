from dataclasses import dataclass


@dataclass(frozen=True)
class UbicacionLlave:
    id: str
    sala: int
    enemigo: str | None = None   # instancia que la suelta; entonces 'sala' es donde inicia
