import gc
import os
import random
import time
import tracemalloc

from bench.cripta_sintetica import crear_partida
from estructuras.ordenamientos import ordenar
from modelo.linea_tiempo import LineaTiempo

ACCIONES = 5000
CONSULTAS = 40
LIMITE_MS = 50
SIN_PUNTOS = 10 ** 9          # un solo punto de control, al principio


def jugar(estado, acciones, semilla=21):
    """Partida determinista: el jugador se mueve por salidas abiertas o espera."""
    azar = random.Random(semilla)
    for _ in range(acciones):
        sala = estado.esqueleto.obtener(estado.jugador.sala)
        abiertas = [s.direccion for s in sala.salidas
                    if estado.esqueleto.puede_atravesar(sala.id, s.direccion)]
        if abiertas and azar.random() < 0.7:
            estado.mover_jugador(abiertas[azar.randrange(len(abiertas))])
        else:
            estado.esperar()
        estado.avanzar_hasta_turno_jugador()


def referencia():
    """Cripta de referencia con todo su contenido cargado y todos sus enemigos activos."""
    from bench.bench_ciclo import cripta_de_referencia
    return cripta_de_referencia().estado


def sintetica():
    return crear_partida(20, 20, 150, semilla=3, cazadores=15, rango=600, con_costos=True)


def medir(crear, cada, consultas):
    gc.collect()
    estado = crear()
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    estado.linea = LineaTiempo(cada, primera=estado.acciones + 1)
    inicio = time.perf_counter()
    jugar(estado, ACCIONES)
    jugada = time.perf_counter() - inicio
    gc.collect()
    memoria = tracemalloc.get_traced_memory()[0] - base
    tracemalloc.stop()
    azar = random.Random(cada % 997)
    tiempos = []
    for i in range(consultas):
        inicio = time.perf_counter()
        if i % 2 == 0:
            estado.linea.estado_antes_de(estado, azar.randrange(1, ACCIONES + 1))
        else:
            estado.linea.estado_en(estado, azar.randrange(0, estado.tiempo))
        tiempos.append((time.perf_counter() - inicio) * 1000)
    tiempos = ordenar(tiempos, lambda v: v)
    return memoria, len(estado.linea.puntos), len(estado.linea.operaciones), tiempos, jugada


def comparar_k(nombre, crear, valores):
    print("== Línea de tiempo en %s: %d acciones, memoria y consulta según K (límite %d ms) =="
          % (nombre, ACCIONES, LIMITE_MS))
    print("%-10s %8s %12s %12s %12s %10s %10s %12s %8s"
          % ("K", "puntos", "operaciones", "memoria KB", "promedio ms", "p95 ms", "máximo ms",
             "partida s", "cumple"))
    for cada in valores:
        consultas = CONSULTAS if cada != SIN_PUNTOS else 4
        memoria, puntos, operaciones, tiempos, jugada = medir(crear, cada, consultas)
        etiqueta = "sin puntos" if cada == SIN_PUNTOS else str(cada)
        p95 = tiempos[max(0, int(len(tiempos) * 0.95) - 1)]
        print("%-10s %8d %12d %12.0f %12.2f %10.2f %10.2f %12.1f %8s"
              % (etiqueta, puntos, operaciones, memoria / 1024, sum(tiempos) / len(tiempos), p95,
                 tiempos[-1], jugada, "si" if p95 < LIMITE_MS else "NO"))
    print("('sin puntos' guarda solo la copia del inicio: cada consulta re-simula desde ahí;"
          " 'cumple' mira el p95)")


def medir_punto_en_referencia():
    if not os.path.isdir("datos_offline"):
        return
    from bench.bench_ciclo import cripta_de_referencia
    controlador = cripta_de_referencia()
    estado = controlador.estado
    for _ in range(20):
        controlador.ejecutar("esperar")
    tiempos = []
    for _ in range(20):
        inicio = time.perf_counter()
        estado.copiar()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    tiempos = ordenar(tiempos, lambda v: v)
    print("\n== Un punto de control en la cripta de referencia (todos sus enemigos activos) ==")
    print("copia completa: promedio %.2f ms, máximo %.2f ms (una vez cada K acciones)"
          % (sum(tiempos) / len(tiempos), tiempos[-1]))


def principal():
    if os.path.isdir("datos_offline"):
        comparar_k("la cripta de referencia", referencia, (10, 25, 50, 200, SIN_PUNTOS))
        medir_punto_en_referencia()
    print()
    comparar_k("una cripta sintética más pesada (400 salas, 150 enemigos activos)", sintetica,
               (25,))


if __name__ == "__main__":
    principal()
