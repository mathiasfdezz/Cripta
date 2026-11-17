class PuertaBloqueada:
    """Una salida cerrada que la verificación no pudo cruzar: de qué sala sale, hacia
    dónde, qué llave pide (None si no declara ninguna) y dónde está esa llave."""

    def __init__(self, sala, direccion, destino, llave, ubicaciones):
        self.sala = sala
        self.direccion = direccion
        self.destino = destino
        self.llave = llave
        self.ubicaciones = tuple(ubicaciones)   # UbicacionLlave de esa llave

    def __repr__(self):
        return f"PuertaBloqueada({self.sala} {self.direccion} -> {self.destino}, {self.llave})"
