from estructuras.fila import Fila


class Bitacora:

    def __init__(self, maximo=20):
        self._mensajes = Fila(maximo, sobrescribir=True)

    def agregar(self, texto):
        self._mensajes.encolar(texto)

    def ultimos(self):
        """Del mas antiguo al mas reciente."""
        return list(self._mensajes)

    def __len__(self):
        return len(self._mensajes)