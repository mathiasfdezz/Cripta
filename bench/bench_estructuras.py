import random
import time

from dtos.ficha_catalogo import FichaCatalogo
from modelo.agenda_eventos import AgendaEventos
from modelo.cache_catalogo import CacheCatalogo
from modelo.evento import Evento
from modelo.inventario import Inventario


class _FuenteFalsa:
    def catalogo(self, ids):
        return tuple(FichaCatalogo(id=i, nombre=i, clase="arma", peso=1, valor=1, ataque_bonus=1)
                     for i in ids)


def _objeto(i):
    return FichaCatalogo(id="itm_%d" % i, nombre="Objeto %d" % i, clase="arma",
                         peso=1 + i % 5, valor=10 + i % 7, ataque_bonus=1)


def _us(funcion, repeticiones):
    t0 = time.perf_counter()
    for i in range(repeticiones):
        funcion(i)
    return (time.perf_counter() - t0) / repeticiones * 1e6


def bench_cache():
    ids = ["ent_%d" % i for i in range(500)]
    cache = CacheCatalogo(_FuenteFalsa(), capacidad=25)
    cache.resolver(ids[:20])
    acierto = _us(lambda i: cache.resolver([ids[i % 20]]), 20000)
    fallo = _us(lambda i: cache.resolver([ids[100 + i % 400]]), 5000)
    print("== Cache de catalogo (us por consulta, tope 25) ==")
    print("acierto (en memoria)     %10.2f" % acierto)
    print("fallo (desaloja y pide)  %10.2f" % fallo)


def _medir_soltar(n, posicion, repeticiones):
    total = 0.0
    for _ in range(repeticiones):
        inv = Inventario(n)
        for i in range(n):
            inv.recoger(_objeto(i))
        for _ in range(posicion):
            inv.avanzar()
        t0 = time.perf_counter()
        inv.soltar_actual()
        total += time.perf_counter() - t0
    return total / repeticiones * 1e6


def bench_inventario():
    print("== Inventario: soltar (us) segun la posicion ==")
    for n in (10, 1000):
        repeticiones = 2000 if n <= 100 else 100
        for nombre, posicion in (("frente", 0), ("medio", n // 2), ("fondo", n - 1)):
            print("n=%5d  %-7s %10.2f" % (n, nombre, _medir_soltar(n, posicion, repeticiones)))


def bench_agenda():
    print("== Agenda de eventos (us por programar + sacar) ==")
    azar = random.Random(42)
    for n in (300, 3000):
        agenda = AgendaEventos()
        for i in range(n):
            agenda.programar(i, Evento("accion", "jugador"))
        us = _us(lambda i: (agenda.programar(azar.randrange(n), Evento("accion", "jugador")),
                            agenda.sacar_siguiente()), 20000)
        print("n=%5d  %10.2f" % (n, us))


def principal():
    bench_cache()
    print()
    bench_inventario()
    print()
    bench_agenda()


if __name__ == "__main__":
    principal()