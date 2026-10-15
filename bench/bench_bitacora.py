import sys

from bench.cronometro import medir_us
from modelo.bitacora import Bitacora

MENSAJES = 100000
MAXIMO = 20


class _ListaQueDesplaza:
    """Alternativa descartada: lista con append y pop(0). La memoria queda fija, pero cada
    mensaje nuevo mueve físicamente los 19 anteriores."""

    def __init__(self):
        self._mensajes = []

    def agregar(self, texto):
        self._mensajes.append(texto)
        if len(self._mensajes) > MAXIMO:
            self._mensajes.pop(0)


class _ListaQueCrece:
    """Alternativa descartada: se guarda todo y se muestran los últimos 20."""

    def __init__(self):
        self._mensajes = []

    def agregar(self, texto):
        self._mensajes.append(texto)


def _medir(bitacora, interna):
    tiempo = medir_us(lambda i: bitacora.agregar("mensaje"), MENSAJES)
    return tiempo, sys.getsizeof(interna(bitacora))


def principal():
    print("== Bitacora de %d mensajes: costo de agregar y memoria tras %d mensajes =="
          % (MAXIMO, MENSAJES))
    print("%-26s %14s %14s %16s" % ("estructura", "us/agregar", "bytes", "desplaza"))
    filas = (
        ("fila circular (la nuestra)", Bitacora(MAXIMO), lambda b: b._mensajes._datos, "no"),
        ("lista con pop(0)", _ListaQueDesplaza(), lambda b: b._mensajes, "19 por mensaje"),
        ("lista que crece", _ListaQueCrece(), lambda b: b._mensajes, "no"),
    )
    for nombre, bitacora, interna, desplaza in filas:
        tiempo, memoria = _medir(bitacora, interna)
        print("%-26s %14.3f %14d %16s" % (nombre, tiempo, memoria, desplaza))


if __name__ == "__main__":
    principal()
