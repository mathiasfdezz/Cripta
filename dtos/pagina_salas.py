from dataclasses import dataclass


@dataclass(frozen=True)
class PaginaSalas:
    pagina: int
    total_paginas: int
    salas: tuple  # de Sala