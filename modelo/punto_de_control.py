class PuntoDeControl:
    """Copia completa del estado justo antes de la acción número 'accion' del jugador.
    'operacion' es la posición de la línea de tiempo donde empieza esa acción."""

    def __init__(self, accion, operacion, estado):
        self.accion = accion
        self.operacion = operacion
        self.estado = estado
