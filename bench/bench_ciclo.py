import gc
import os
import time

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.cliente_offline import ClienteOffline
from bench.cripta_sintetica import crear_partida
from controlador.partida import ControladorPartida
from estructuras.ordenamientos import ordenar
from modelo.cache_catalogo import CacheCatalogo

LIMITE_MS = 20
CICLOS = 200


class _VistaNula:
    """El bench no dibuja nada: el enunciado mide sin renderizado."""

    def mostrar_partida(self, *args):
        pass

    def mostrar_resultado(self, *args):
        pass

    def mostrar_objeto_actual(self, *args):
        pass

    def mostrar_inventario_detallado(self, *args):
        pass

    def mostrar_ayuda(self):
        pass

    def mostrar_fin(self, *args):
        pass


def _medir(funcion, estado):
    """Tiempo de cada ciclo y cuántos eventos se ejecutaron en él."""
    tiempos, eventos = [], 0
    for _ in range(CICLOS):
        antes = estado.agenda.siguiente_secuencia()
        inicio = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
        eventos += estado.agenda.siguiente_secuencia() - antes
    ordenados = ordenar(tiempos, lambda t: t)
    promedio = sum(tiempos) / len(tiempos)
    p95 = ordenados[int(len(ordenados) * 0.95) - 1]
    por_evento = promedio * 1000 / max(1, eventos / CICLOS)
    return promedio, p95, ordenados[-1], eventos / CICLOS, por_evento


def _fila(escenario, medicion):
    promedio, p95, maximo, eventos, por_evento = medicion
    cumple = "si" if maximo < LIMITE_MS else ("p95" if p95 < LIMITE_MS else "NO")
    print("%-30s %9.2f %9.2f %9.2f %10.0f %10.1f %7s"
          % (escenario, promedio, p95, maximo, eventos, por_evento, cumple))


def _ciclo_motor(estado):
    def ciclo():
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()
    return ciclo


def principal():
    print("== Ciclo completo entre dos decisiones del jugador (ms, limite %d) ==" % LIMITE_MS)
    print("%-30s %9s %9s %9s %10s %10s %7s" % ("escenario", "promedio", "p95", "maximo",
                                               "eventos", "us/evento", "cumple"))

    if os.path.isdir("datos_offline"):
        fuente = ClienteOffline()
        # la cripta de referencia es la primera del paquete offline
        datos = fuente.datos_cripta(fuente.listar_criptas()[0].id)
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco("cache_catalogo"))
        cache.validar_version(fuente.version_catalogo())
        controlador = ControladorPartida(datos, fuente, cache, _VistaNula(), 1)
        # que no termine durante la medición
        controlador.estado.jugador.vida = 10 ** 9
        _fila(f"{datos.id} (controlador)", _medir(lambda: controlador.ejecutar("esperar"),
                                                  controlador.estado))

    for filas, columnas, enemigos in ((10, 10, 100), (20, 20, 400), (25, 25, 600),
                                      (30, 30, 900)):
        estado = crear_partida(filas, columnas, enemigos)
        # igual que hace el controlador del juego después de cargar la cripta
        gc.freeze()
        _fila(f"{filas * columnas} salas, {enemigos} enemigos", _medir(_ciclo_motor(estado), estado))
    print("(eventos = eventos programados por ciclo; 'p95': cumple en el 95% de los ciclos)")


if __name__ == "__main__":
    principal()