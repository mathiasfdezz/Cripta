# motivos por los que el jugador no puede mover ni abrir una puerta
NO_ES_TURNO = "no_es_turno"
SIN_MAPA = "sin_mapa"
SIN_SALIDA = "sin_salida"
SALA_NO_DISPONIBLE = "sala_no_disponible"
PUERTA_CERRADA = "puerta_cerrada"
PUERTA_ABIERTA = "puerta_abierta"
SIN_LLAVE = "sin_llave"


class MovimientoInvalido(ValueError):
    """Una acción del mapa rechazada. No gasta tiempo ni cambia nada.
    motivo es una de las constantes de este módulo."""

    def __init__(self, motivo, mensaje):
        super().__init__(mensaje)
        self.motivo = motivo