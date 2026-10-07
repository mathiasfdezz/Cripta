# motivos por los que se rechaza una acción del jugador
NO_ES_TURNO = "no_es_turno"
PARTIDA_TERMINADA = "partida_terminada"
CONTENIDO_PENDIENTE = "contenido_pendiente"
SIN_ENEMIGO = "sin_enemigo"
NADA_QUE_RECOGER = "nada_que_recoger"
INVENTARIO_LLENO = "inventario_lleno"
SIN_OBJETO = "sin_objeto"
NO_EQUIPABLE = "no_equipable"
NO_USABLE = "no_usable"
SIN_PERGAMINO = "sin_pergamino"
NADA_QUE_DESHACER = "nada_que_deshacer"
SIN_MAPA = "sin_mapa"
SIN_SALIDA = "sin_salida"
SALA_NO_DISPONIBLE = "sala_no_disponible"
PUERTA_CERRADA = "puerta_cerrada"
PUERTA_ABIERTA = "puerta_abierta"
SIN_LLAVE = "sin_llave"


class MovimientoInvalido(ValueError):
    """Una acción del jugador rechazada. No gasta tiempo ni cambia nada.
    motivo es una de las constantes de este módulo."""

    def __init__(self, motivo, mensaje):
        super().__init__(mensaje)
        self.motivo = motivo