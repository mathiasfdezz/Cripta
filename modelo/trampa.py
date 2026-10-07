class Trampa:
    """Una trampa concreta de una sala. La ficha del catálogo dice su daño y cada
    cuánto se rearma; aquí solo vive su estado en la partida."""

    def __init__(self, instancia, tipo, sala, armada=True):
        self.instancia = instancia
        self.tipo = tipo
        self.sala = sala
        self.armada = armada