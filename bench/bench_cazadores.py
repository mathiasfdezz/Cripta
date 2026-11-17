import random
import time

from bench.cripta_sintetica import crear_esqueleto
from bench.ruta_por_cazador import RutaPorCazador
from modelo.buscador_rutas import BuscadorRutas

LADO = 30                 # cuadrícula de 900 salas con costos variados
POSICIONES = 25           # salas del jugador distintas por medición
RONDAS = 300


def _decidir_compartido(buscador, objetivo, cazadores, rango):
    buscador.calcular(objetivo, rango)
    pasos = []
    for desde in cazadores:
        d = buscador.distancia(desde)
        pasos.append(None if d is None or d > rango or desde == objetivo
                     else buscador.primer_paso(desde, d))
    return pasos


def _decidir_individual(alternativa, objetivo, cazadores, rango):
    return [None if desde == objetivo else alternativa.decidir(desde, objetivo, rango)
            for desde in cazadores]


def comparar_compartido_individual():
    print("== Ruta del cazador: un cálculo compartido frente a uno por cazador "
          "(ms por ronda de decisiones, %d salas) ==" % (LADO * LADO))
    print("%-10s %-7s %12s %12s %10s %14s %14s"
          % ("cazadores", "rango", "compartido", "individual", "razón", "salas/compart.",
             "salas/indiv."))
    esqueleto = crear_esqueleto(LADO, LADO, semilla=3, con_costos=True)
    grafo = esqueleto.grafo()
    n = grafo.cantidad_salas()
    for rango in (300, 2400):
        for cantidad in (1, 10, 30, 60):
            azar = random.Random(cantidad * 1000 + rango)
            buscador = BuscadorRutas(grafo, esqueleto.salida_abierta)
            alternativa = RutaPorCazador(grafo, esqueleto.salida_abierta)
            t_compartido = t_individual = 0.0
            for _ in range(POSICIONES):
                objetivo = azar.randrange(n)
                # cazadores cerca del jugador, como cuando ya están persiguiéndolo
                cazadores = [_cerca(azar, objetivo, LADO, 6) for _ in range(cantidad)]
                inicio = time.perf_counter()
                a = _decidir_compartido(buscador, objetivo, cazadores, rango)
                t_compartido += time.perf_counter() - inicio
                inicio = time.perf_counter()
                b = _decidir_individual(alternativa, objetivo, cazadores, rango)
                t_individual += time.perf_counter() - inicio
                if a != b:
                    raise AssertionError("las dos búsquedas no deciden lo mismo")
            compartido = t_compartido * 1000 / POSICIONES
            individual = t_individual * 1000 / POSICIONES
            print("%-10d %-7d %12.3f %12.3f %10.1f %14.0f %14.0f"
                  % (cantidad, rango, compartido, individual, individual / compartido,
                     buscador.salas_asentadas / POSICIONES,
                     alternativa.salas_asentadas / POSICIONES))
    print("(las dos alternativas deciden exactamente lo mismo; se verifica en cada ronda)")


def _cerca(azar, objetivo, lado, radio):
    fila, columna = divmod(objetivo, lado)
    fila = min(lado - 1, max(0, fila + azar.randrange(-radio, radio + 1)))
    columna = min(lado - 1, max(0, columna + azar.randrange(-radio, radio + 1)))
    return fila * lado + columna


def comparar_invalidacion():
    print("\n== Invalidación: reutilizar el cálculo frente a recalcular siempre "
          "(30 cazadores, rango 2400, %d rondas) ==" % RONDAS)
    print("%-22s %-14s %12s %10s %12s" % ("puertas", "estrategia", "ms/ronda", "cálculos",
                                         "reutilizados"))
    for nombre, cambios_por_ronda in (("estables (1 c/50)", 0.02), ("inestables (8/ronda)", 8)):
        resultados = []
        for estrategia in ("reutilizar", "recalcular"):
            esqueleto = crear_esqueleto(LADO, LADO, semilla=5, con_costos=True)
            grafo = esqueleto.grafo()
            azar = random.Random(17)
            buscador = BuscadorRutas(grafo, esqueleto.salida_abierta)
            jugador = azar.randrange(grafo.cantidad_salas())
            cazadores = [_cerca(azar, jugador, LADO, 8) for _ in range(30)]
            total = 0.0
            decisiones = []
            for ronda in range(RONDAS):
                for _ in range(_cuantos(azar, cambios_por_ronda)):
                    puerta = esqueleto.puerta_de_salida(azar.randrange(grafo.cantidad_salidas()))
                    puerta.cerrar() if puerta.esta_abierta() else puerta.abrir()
                if ronda % 4 == 0:
                    vecinas = [d for d, _, s in grafo.salientes[jugador]
                               if esqueleto.salida_abierta(s)]
                    if vecinas:
                        jugador = vecinas[azar.randrange(len(vecinas))]
                inicio = time.perf_counter()
                for i, desde in enumerate(cazadores):
                    if estrategia == "reutilizar":
                        buscador.asegurar(jugador, 2400, *esqueleto.tomar_cambios())
                    else:
                        buscador.calcular(jugador, 2400)
                    d = buscador.distancia(desde)
                    if d is not None and desde != jugador:
                        paso = buscador.primer_paso(desde, d)
                        cazadores[i] = paso[0]
                total += time.perf_counter() - inicio
                decisiones.append(tuple(cazadores))
            resultados.append(decisiones)
            print("%-22s %-14s %12.3f %10d %12d" % (nombre, estrategia, total * 1000 / RONDAS,
                                                    buscador.calculos, buscador.reutilizados))
        if resultados[0] != resultados[1]:
            raise AssertionError("reutilizar cambió alguna decisión")
    print("(en los dos casos las decisiones de todas las rondas son idénticas)")


def _cuantos(azar, promedio):
    if promedio >= 1:
        return int(promedio)
    return 1 if azar.random() < promedio else 0


def principal():
    comparar_compartido_individual()
    comparar_invalidacion()


if __name__ == "__main__":
    principal()
