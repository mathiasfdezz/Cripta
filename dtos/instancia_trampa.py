from dataclasses import dataclass


@dataclass(frozen=True)
class InstanciaTrampa:
    instancia: str
    tipo: str