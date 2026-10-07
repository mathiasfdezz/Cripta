from contextlib import contextmanager

from estructuras.lista_doble import ListaDoble
from estructuras.pila import Pila

MAX_ACCIONES = 5


class Historial:
    """Cómo deshacer las últimas acciones del jugador (máximo 5).

    Cada acción abre un intervalo: una Pila con la forma de deshacer cada cambio
    que ocurra hasta la siguiente decisión del jugador (su acción y todo lo que
    hagan después enemigos y efectos). No se copia el estado: solo se guarda el
    valor anterior de lo que cambió."""

    def __init__(self, maximo=MAX_ACCIONES):
        self._maximo = maximo
        self._intervalos = ListaDoble()   # el más reciente queda al final
        self._grabando = True

    def abrir_intervalo(self):
        self._intervalos.agregar_final(Pila())
        if len(self._intervalos) > self._maximo:
            # se descarta lo más antiguo
            self._intervalos.eliminar_nodo(self._intervalos.cabeza)

    def registrar(self, deshacer):
        """deshacer: función sin argumentos que revierte un cambio."""
        if self._grabando and not self._intervalos.esta_vacia():
            self._intervalos.cola.dato.apilar(deshacer)

    def deshacer(self):
        """Revierte el último intervalo completo. False si no hay nada que deshacer."""
        if self._intervalos.esta_vacia():
            return False
        pila = self._intervalos.eliminar_nodo(self._intervalos.cola)
        with self.sin_registrar():
            # en orden inverso: lo último que cambió es lo primero que se deshace
            while not pila.esta_vacia():
                pila.desapilar()()
        return True

    def acciones_guardadas(self):
        return len(self._intervalos)

    @contextmanager
    def sin_registrar(self):
        anterior = self._grabando
        self._grabando = False
        try:
            yield
        finally:
            self._grabando = anterior
