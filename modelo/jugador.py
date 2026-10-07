from modelo.actor import Actor

ID_JUGADOR = "jugador"   # el mismo objetivo que usan los Evento del jugador


class Jugador(Actor):
    def __init__(self, sala, estadisticas, inventario):
        # estadisticas: EstadisticasJugador, inventario: Inventario
        super().__init__(ID_JUGADOR, sala, estadisticas.vida_max, estadisticas.ataque,
                         estadisticas.defensa, estadisticas.velocidad)
        self.inventario = inventario

    def ataque_efectivo(self):
        # el arma equipada suma su bonus
        return self.ataque + (self.inventario.bonus_ataque() or 0)

    def defensa_efectiva(self):
        # la armadura equipada suma su bonus
        return self.defensa + (self.inventario.bonus_defensa() or 0)

    def puede_abrir(self, puerta):
        # abre una puerta quien tenga la llave que ella pide; la llave no se gasta
        return puerta.llave is not None and self.inventario.tiene_objeto_id(puerta.llave)