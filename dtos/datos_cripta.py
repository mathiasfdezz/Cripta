from dataclasses import dataclass

from dtos.estadisticas_jugador import EstadisticasJugador


@dataclass(frozen=True)
class DatosCripta:
    id: str
    version: str
    salas_total: int
    paginas: int
    salas_por_pagina: int
    sala_inicial: int
    sala_salida: int
    llave_salida: str
    presupuesto_solicitudes: int
    inventario_max: int
    jugador: EstadisticasJugador