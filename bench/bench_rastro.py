import random

from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from bench.cronometro import medir_us
from bench.rastreo_por_bfs import decidir_con_bfs
from modelo.esqueleto import Esqueleto
from modelo.rastro import Rastro

DECISIONES = 2000


def _cuadricula(lado):
    salas = []
    for fila in range(lado):
        for columna in range(lado):
            id_sala = fila * lado + columna + 1
            salidas = {}
            if fila > 0:
                salidas["N"] = {"sala": id_sala - lado}
            if fila < lado - 1:
                salidas["S"] = {"sala": id_sala + lado}
            if columna < lado - 1:
                salidas["E"] = {"sala": id_sala + 1}
            if columna > 0:
                salidas["O"] = {"sala": id_sala - 1}
            salas.append({"id": id_sala, "nombre": f"S{id_sala}", "salidas": salidas})
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina(pagina_salas_desde_json(
        {"pagina": 1, "total_paginas": 1, "salas": salas}))
    return esqueleto


def _recorrido(esqueleto, rastro, lado, azar):
    # el jugador camina al azar 300 pasos de 100 unidades y deja su rastro
    sala, tiempo = 1, 0
    for _ in range(300):
        rastro.marcar(sala, tiempo)
        salidas = esqueleto.obtener(sala).salidas
        sala = salidas[azar.randrange(len(salidas))].sala_destino
        tiempo += 100
    return tiempo


def principal():
    print("== Decision de un rastreador: vecinas de su sala vs BFS por la cripta (us) ==")
    print("%8s %16s %16s %14s %10s" % ("salas", "1a vez en sala", "sala ya vista", "BFS",
                                       "BFS/vista"))
    for lado in (10, 30, 50):
        azar = random.Random(lado)
        esqueleto = _cuadricula(lado)
        rastro = Rastro(esqueleto)
        ahora = _recorrido(esqueleto, rastro, lado, azar)
        salas = lado * lado
        # la primera consulta de cada sala enlaza sus vecinas; pasa una vez por sala
        nuevas = list(range(1, salas + 1))
        azar.shuffle(nuevas)
        primera = medir_us(lambda i: rastro.sala_mas_fresca(nuevas[i], ahora), salas)
        origenes = [azar.randrange(1, salas + 1) for _ in range(DECISIONES)]
        vista = medir_us(lambda i: rastro.sala_mas_fresca(origenes[i], ahora), DECISIONES)
        repeticiones = max(20, DECISIONES * 100 // salas)
        bfs = medir_us(lambda i: decidir_con_bfs(esqueleto, rastro, origenes[i], ahora),
                       repeticiones)
        print("%8d %16.2f %16.2f %14.2f %10.0f" % (salas, primera, vista, bfs, bfs / vista))


if __name__ == "__main__":
    principal()
