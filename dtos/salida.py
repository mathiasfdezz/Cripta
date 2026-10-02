from dataclasses import dataclass


@dataclass(frozen=True)
class Salida:
    direccion: str
    sala_destino: int
    cerrada: bool = False
    llave: str | None = None
    cierre_automatico: int | None = None