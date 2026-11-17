import os
import random
import time

from bench.cripta_sintetica import crear_esqueleto
from bench.ruta_por_cazador import RutaPorCazador
from estructuras.vector_ordenado import VectorOrdenado
from modelo.buscador_rutas import BuscadorRutas
from modelo.estado_partida import SIN_COTA
from modelo.mapa_conocido import MapaConocido

CONSULTAS = 200_000
VIAJES = 300
LIMITE_PASO_MS = 5


def comparar_consultas():
    print("== Mapa conocido: consultar el estado de una sala (ns por consulta) ==")
    print("%-12s %16s %22s" % ("exploradas", "lista por índice", "VectorOrdenado de ids"))
    for exploradas in (50, 300, 900):
        esqueleto = crear_esqueleto(30, 30)
        grafo = esqueleto.grafo()
        mapa = MapaConocido(grafo)
        vector = VectorOrdenado()
        azar = random.Random(exploradas)
        for indice in azar.sample(range(grafo.cantidad_salas()), exploradas):
            mapa.explorar(indice, esqueleto.salida_cerrada)
            vector.insertar(grafo.ids[indice], True)
        preguntas = [azar.randrange(grafo.cantidad_salas()) for _ in range(CONSULTAS)]
        ids = grafo.ids
        inicio = time.perf_counter()
        for i in preguntas:
            mapa.esta_explorada(i)
        lista = time.perf_counter() - inicio
        inicio = time.perf_counter()
        for i in preguntas:
            vector.contiene(ids[i])
        ordenado = time.perf_counter() - inicio
        print("%-12d %16.0f %22.0f" % (exploradas, lista * 1e9 / CONSULTAS,
                                         ordenado * 1e9 / CONSULTAS))


def comparar_exploracion():
    print("\n== Explorar una sala nueva según cuántas hay exploradas (us por sala, 900 salas) ==")
    print("%-24s %16s %22s" % ("tramo", "lista por índice", "VectorOrdenado de ids"))
    esqueleto = crear_esqueleto(30, 30)
    grafo = esqueleto.grafo()
    orden = list(range(grafo.cantidad_salas()))
    random.Random(9).shuffle(orden)
    mapa = MapaConocido(grafo)
    vector = VectorOrdenado()
    tramos = ((0, 90), (405, 495), (810, 900))
    tiempos_lista = [0.0] * len(tramos)
    tiempos_vector = [0.0] * len(tramos)
    for posicion, indice in enumerate(orden):
        inicio = time.perf_counter()
        mapa.explorar(indice, esqueleto.salida_cerrada)
        medio = time.perf_counter()
        # la alternativa guarda explorada y avistadas en vectores ordenados por id
        vector.insertar(grafo.ids[indice], True)
        for destino, _, _ in grafo.salientes[indice]:
            if not vector.contiene(grafo.ids[destino]):
                vector.insertar(-grafo.ids[destino], True)
        fin = time.perf_counter()
        for k, (desde, hasta) in enumerate(tramos):
            if desde <= posicion < hasta:
                tiempos_lista[k] += medio - inicio
                tiempos_vector[k] += fin - medio
    for k, (desde, hasta) in enumerate(tramos):
        print("%-24s %16.2f %22.2f" % (f"salas {desde}-{hasta}", tiempos_lista[k] * 1e6 / 90,
                                       tiempos_vector[k] * 1e6 / 90))


def _cripta_de_referencia():
    if not os.path.isdir("datos_offline"):
        return None
    from adaptadores.cliente_offline import ClienteOffline
    from modelo.esqueleto import Esqueleto
    fuente = ClienteOffline()
    mayor = None
    for cripta in fuente.listar_criptas():
        if mayor is None or cripta.salas > mayor.salas:
            mayor = cripta
    datos = fuente.datos_cripta(mayor.id)
    esqueleto = Esqueleto()
    for pagina in range(1, datos.paginas + 1):
        esqueleto.agregar_pagina(fuente.pagina_salas(datos.id, pagina))
    return mayor.id, esqueleto


def medir_ir_a():
    print("\n== Un paso de «ir a» con el mapa conocido completo (ms, límite %d) ==" % LIMITE_PASO_MS)
    print("%-28s %10s %10s %10s %14s %16s %8s" % ("mapa", "promedio", "p95", "máximo",
                                                 "sin parar", "adelante (prom.)", "cumple"))
    casos = []
    referencia = _cripta_de_referencia()
    if referencia is not None:
        casos.append((f"{referencia[0]} ({referencia[1].grafo().cantidad_salas()} salas)",
                      referencia[1]))
    casos.append(("sintética 900 salas", crear_esqueleto(30, 30, semilla=4, con_costos=True)))
    for nombre, esqueleto in casos:
        grafo = esqueleto.grafo()
        mapa = MapaConocido(grafo)
        for indice in range(grafo.cantidad_salas()):
            mapa.explorar(indice, esqueleto.salida_cerrada)
        buscador = BuscadorRutas(grafo, mapa.recuerda_abierta, mapa.esta_explorada)
        adelante = RutaPorCazador(grafo, mapa.recuerda_abierta)
        azar = random.Random(11)
        tiempos = []
        total_adelante = 0.0
        total_completo = 0.0
        for _ in range(VIAJES):
            desde = azar.randrange(grafo.cantidad_salas())
            hasta = azar.randrange(grafo.cantidad_salas())
            inicio = time.perf_counter()
            buscador.calcular(hasta, SIN_COTA)
            d = buscador.distancia(desde)
            completo = None if d is None or desde == hasta else buscador.primer_paso(desde, d)
            total_completo += time.perf_counter() - inicio
            # lo que hace el juego: se detiene al asentar la sala del jugador
            inicio = time.perf_counter()
            buscador.calcular(hasta, SIN_COTA, hasta=desde)
            d = buscador.distancia(desde)
            paso = None if d is None or desde == hasta else buscador.primer_paso(desde, d)
            tiempos.append((time.perf_counter() - inicio) * 1000)
            if paso != completo:
                raise AssertionError("detenerse antes cambió el paso")
            inicio = time.perf_counter()
            otro = None if desde == hasta else adelante.decidir(desde, hasta, SIN_COTA)
            total_adelante += time.perf_counter() - inicio
            if paso != otro:
                raise AssertionError("las dos búsquedas no dan el mismo paso")
        tiempos = _ordenar(tiempos)
        maximo = tiempos[-1]
        print("%-28s %10.3f %10.3f %10.3f %14.3f %16.3f %8s"
              % (nombre, sum(tiempos) / len(tiempos), tiempos[int(len(tiempos) * 0.95) - 1],
                 maximo, total_completo * 1000 / VIAJES, total_adelante * 1000 / VIAJES,
                 "si" if maximo < LIMITE_PASO_MS else "NO"))
    print("(los tres cálculos dan el mismo paso en todos los viajes; se verifica)")


def _ordenar(valores):
    from estructuras.ordenamientos import ordenar
    return ordenar(valores, lambda v: v)


def principal():
    comparar_consultas()
    comparar_exploracion()
    medir_ir_a()


if __name__ == "__main__":
    principal()
