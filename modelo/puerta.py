class Puerta:
    """El estado de UNA salida de una sala. Cada lado de una conexión tiene la suya
    y son independientes (lo confirmó el profesor): abrir la salida E de la sala 2
    no cambia la salida O de la sala 5."""

    def __init__(self, salida):
        self._cerrada = bool(salida.cerrada)
        self.llave = salida.llave
        self.cierre_automatico = salida.cierre_automatico
        self.costo = salida.costo
        self._cerrada_inicial = self._cerrada
        # los pone el esqueleto al numerar las salidas: así la búsqueda de rutas se
        # entera de qué puerta cambió, también cuando el cambio viene de deshacer
        self.indice = None
        self.al_cambiar = None

    @property
    def cerrada(self):
        return self._cerrada

    @cerrada.setter
    def cerrada(self, valor):
        valor = bool(valor)
        if valor != self._cerrada:
            self._cerrada = valor
            if self.al_cambiar is not None:
                self.al_cambiar(self.indice)

    def esta_cerrada(self):
        return self._cerrada

    def esta_abierta(self):
        return not self._cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def reiniciar(self):
        """Vuelve al estado que declaró el API (antes de cargar una partida guardada)."""
        self.cerrada = self._cerrada_inicial
