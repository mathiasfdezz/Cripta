from dataclasses import dataclass


@dataclass(frozen=True)
class CabeceraPartida:
    cripta_id: str
    version_cripta: str
    version_catalogo: str
    semilla: int
