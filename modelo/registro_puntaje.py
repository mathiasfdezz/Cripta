from dataclasses import dataclass


@dataclass(frozen=True)
class RegistroPuntaje:
    nombre: str
    cripta_id: str
    version_cripta: str
    resultado: str
    acciones: int
    enemigos_derrotados: int
    tiempo_final: int
