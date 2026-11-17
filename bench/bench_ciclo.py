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
        controlador = cripta_de_referencia()
        estado = controlador.estado
        cazadores = sum(1 for e in estado.enemigos_vivos() if e.comportamiento == "cazador")
        _fila(f"{controlador.datos.id} ({cazadores} cazadores)",
              _medir(lambda: controlador.ejecutar("esperar"), estado))
        # el jugador se mueve: cada paso obliga a recalcular las rutas de los cazadores
        _fila(f"{controlador.datos.id} moviéndose", _medir(_ida_y_vuelta(controlador), estado))

    for filas, columnas, enemigos, cazadores in ((10, 10, 100, 0), (20, 20, 400, 0),
                                                 (25, 25, 600, 0), (30, 30, 900, 0),
                                                 (30, 30, 900, 60)):
        estado = crear_partida(filas, columnas, enemigos, cazadores=cazadores, rango=2400,
                               con_costos=cazadores > 0)
        # igual que hace el controlador del juego después de cargar la cripta
        gc.freeze()
        nombre = f"{filas * columnas} salas, {enemigos} enemigos"
        if cazadores:
            nombre = f"{filas * columnas} salas, {cazadores} cazadores"
        _fila(nombre, _medir(_ciclo_motor(estado), estado))
    print("(eventos = eventos programados por ciclo; 'p95': cumple en el 95% de los ciclos)")


def cripta_de_referencia():
    """La cripta más grande del paquete offline (la de referencia), con el contenido de
    todas sus salas cargado y todos sus enemigos activos: el peor caso del §6.1."""
    fuente = ClienteOffline()
    criptas = fuente.listar_criptas()
    mayor = criptas[0]
    for cripta in criptas:
        if cripta.salas > mayor.salas:
            mayor = cripta
    datos = fuente.datos_cripta(mayor.id)
    cache = CacheCatalogo(fuente, AlmacenCatalogoDisco("cache_catalogo"), capacidad=50)
    cache.validar_version(fuente.version_catalogo())
    controlador = ControladorPartida(datos, fuente, cache, _VistaNula(), 1)
    estado = controlador.estado
    ids = estado.esqueleto.grafo().ids
    for i in range(0, len(ids), 10):
        for contenido in fuente.contenido(datos.id, list(ids[i:i + 10])):
            tipos = [e.tipo for e in contenido.enemigos] + list(contenido.objetos)
            cache.resolver(tipos + [t.tipo for t in contenido.trampas] or ["itm_antorcha"])
            estado.cargar_contenido(contenido)
    for enemigo in estado.enemigos_vivos():
        if not enemigo.activo:
            enemigo.activo = True
            estado.programar_accion(enemigo)
    # que no termine durante la medición
    estado.jugador.vida = 10 ** 9
    estado.jugador.defensa = 10 ** 6
    return controlador


def _ida_y_vuelta(controlador):
    def ciclo():
        estado = controlador.estado
        sala = estado.esqueleto.obtener(estado.jugador.sala)
        for salida in sala.salidas:
            if estado.esqueleto.puede_atravesar(sala.id, salida.direccion):
                controlador.ejecutar(salida.direccion.lower())
                return
        controlador.ejecutar("esperar")
    return ciclo


if __name__ == "__main__":
    principal()