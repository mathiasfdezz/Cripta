import time

from bench.cripta_sintetica import crear_partida
from dtos.ficha_catalogo import FichaCatalogo

PERGAMINO = FichaCatalogo(id="itm_perg", nombre="Pergamino", clase="pergamino_retroceso",
                          peso=1, valor=40)
RONDAS = 50


def principal():
    print("== Historial de retroceso (por accion del jugador) ==")
    print("%-26s %13s %15s %18s" % ("escenario", "accion (us)", "deshacer (us)",
                                    "cambios guardados"))
    for filas, columnas, enemigos in ((10, 10, 100), (20, 20, 400)):
        estado = crear_partida(filas, columnas, enemigos)
        estado.jugador.inventario.recoger(PERGAMINO)
        accion, deshacer, cambios = 0.0, 0.0, 0
        for _ in range(RONDAS):
            inicio = time.perf_counter()
            estado.esperar()
            estado.avanzar_hasta_turno_jugador()
            accion += time.perf_counter() - inicio
            cambios += estado.historial.cambios_ultima_accion()
            inicio = time.perf_counter()
            estado.deshacer()
            deshacer += time.perf_counter() - inicio
            estado.jugador.inventario.recoger(PERGAMINO)
        escenario = f"{filas * columnas} salas, {enemigos} enemigos"
        print("%-26s %13.1f %15.1f %18.1f" % (escenario, accion / RONDAS * 1e6,
                                              deshacer / RONDAS * 1e6, cambios / RONDAS))
    print("(se guarda solo lo que cambio en cada intervalo, nunca una copia del estado)")


if __name__ == "__main__":
    principal()