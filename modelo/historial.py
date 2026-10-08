from contextlib import contextmanager

from estructuras.lista_doble import ListaDoble
from estructuras.pila import Pila

MAX_ACCIONES = 5


class Historial:
    """Cómo deshacer las últimas acciones del jugador (máximo 5).

    Cada acción abre un intervalo: una Pila con la forma de deshacer cada cambio
    que ocurra hasta la siguiente decisión del jugador (su acción y todo lo que
    hagan después enemigos y efectos). No se copia el estado: solo se guarda el
    valor anterior de lo que cambió.

    Un cambio se guarda de dos formas: (objeto, atributo, valor anterior), que es
    lo más común y lo más barato, o una función que sabe deshacerlo."""

    def __init__(self, maximo=MAX_ACCIONES):
        self._maximo = maximo
        self._intervalos = ListaDoble()   # el más reciente queda al final
        self._actual = None               # Pila donde se anota; None si no se anota
        self._numero = 0                  # número del intervalo abierto; nunca se repite

    def abrir_intervalo(self):
        self._numero += 1
        self._actual = Pila()
        self._intervalos.agregar_final(self._actual)
        if len(self._intervalos) > self._maximo:
            # se descarta lo más antiguo
            self._intervalos.eliminar_nodo(self._intervalos.cabeza)

    def registrar(self, deshacer):
        """deshacer: función sin argumentos que revierte un cambio."""
        if self._actual is not None:
            self._actual.apilar(deshacer)

    def registrar_valor(self, objeto, atributo, anterior):
        """El atributo de ese objeto valía 'anterior' antes del cambio."""
        if self._actual is not None:
            self._actual.apilar((objeto, atributo, anterior))

    def deshacer(self):
        """Revierte el último intervalo completo. False si no hay nada que deshacer."""
        if self._intervalos.esta_vacia():
            return False
        pila = self._intervalos.eliminar_nodo(self._intervalos.cola)
        with self.sin_registrar():
            # en orden inverso: lo último que cambió es lo primero que se deshace
            while not pila.esta_vacia():
                cambio = pila.desapilar()
                if isinstance(cambio, tuple):
                    setattr(cambio[0], cambio[1], cambio[2])
                else:
                    cambio()
        # lo que pase hasta la próxima acción del jugador ya no se anota
        self._actual = None
        return True

    def intervalo_actual(self):
        """Número del intervalo donde se está anotando, o None si no se anota."""
        return None if self._actual is None else self._numero

    def acciones_guardadas(self):
        return len(self._intervalos)

    def cambios_ultima_accion(self):
        return 0 if self._intervalos.esta_vacia() else len(self._intervalos.cola.dato)

    @contextmanager
    def sin_registrar(self):
        anterior = self._actual
        self._actual = None
        try:
            yield
        finally:
            self._actual = anterior