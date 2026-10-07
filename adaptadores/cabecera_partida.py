from dataclasses import dataclass


@dataclass(frozen=True)
class CabeceraPartida:
    cripta_id: str
    version_cripta: str
    version_catalogo: str
    semilla: int
    reproducible: bool = True   # False si viene de un guardado sin su bitácora original
