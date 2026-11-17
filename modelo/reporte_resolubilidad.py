class ReporteResolubilidad:
    """Resultado de la verificación (§3.5). Si es resoluble, el orden de las llaves;
    si no, lo que falta, la frontera bloqueada y el ciclo si lo hay."""

    def __init__(self, resoluble, orden_llaves, no_obtenibles=(), frontera=(), ciclo=(),
                 puertas_del_ciclo=(), sin_ubicacion=(), salas=0, salidas=0, llaves=0):
        self.resoluble = resoluble
        self.orden_llaves = tuple(orden_llaves)
        self.no_obtenibles = tuple(no_obtenibles)
        self.frontera = tuple(frontera)              # PuertaBloqueada
        self.ciclo = tuple(ciclo)                    # (k1, k2, ..., k1) o vacío
        self.puertas_del_ciclo = tuple(puertas_del_ciclo)
        self.sin_ubicacion = tuple(sin_ubicacion)    # llaves que piden puertas y ninguna sala tiene
        self.salas = salas
        self.salidas = salidas
        self.llaves = llaves
