class Puerta:
    """El estado de UNA salida de una sala. Cada lado de una conexión tiene la suya
    y son independientes (lo confirmó el profesor): abrir la salida E de la sala 2
    no cambia la salida O de la sala 5."""

    def __init__(self, salida):
        self.cerrada = bool(salida.cerrada)
        self.llave = salida.llave
        self.cierre_automatico = salida.cierre_automatico
        self._cerrada_inicial = self.cerrada

    def esta_cerrada(self):
        return self.cerrada

    def esta_abierta(self):
        return not self.cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def reiniciar(self):
        """Vuelve al estado que declaró el API (antes de cargar una partida guardada)."""
        self.cerrada = self._cerrada_inicial
