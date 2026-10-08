import random

from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.esqueleto import Esqueleto
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador

COMPORTAMIENTOS = ("guardián", "errante", "rastreador")
FICHAS = tuple(FichaCatalogo(id=f"ent_{c}", nombre=c, clase="enemigo", vida_max=10 ** 6,
                             ataque=1, defensa=0, velocidad=v, comportamiento=c)
               for c, v in zip(COMPORTAMIENTOS, (90, 120, 150)))


def _ficha(id_ficha):
    for ficha in FICHAS:
        if ficha.id == id_ficha:
            return ficha
    raise KeyError(id_ficha)


def _sala(fila, columna, filas, columnas):
    id_sala = fila * columnas + columna + 1
    salidas = {}
    if fila > 0:
        salidas["N"] = {"sala": id_sala - columnas}
    if fila < filas - 1:
        salidas["S"] = {"sala": id_sala + columnas}
    if columna < columnas - 1:
        salidas["E"] = {"sala": id_sala + 1}
    if columna > 0:
        salidas["O"] = {"sala": id_sala - 1}
    return {"id": id_sala, "nombre": f"S{id_sala}", "salidas": salidas}


def crear_partida(filas, columnas, enemigos, semilla=1):
    """Cuadrícula de salas abiertas con muchos enemigos ya activos: para medir el
    motor sin red ni vista. El jugador empieza en el centro y casi no recibe daño."""
    salas = [_sala(f, c, filas, columnas) for f in range(filas) for c in range(columnas)]
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina(pagina_salas_desde_json(
        {"pagina": 1, "total_paginas": 1, "salas": salas}))
    centro = (filas // 2) * columnas + columnas // 2 + 1
    jugador = Jugador(centro, EstadisticasJugador(10 ** 9, 5, 10 ** 6, 100), Inventario(10))
    estado = EstadoPartida(semilla, jugador, esqueleto, obtener_ficha=_ficha)
    azar = random.Random(semilla)
    por_sala = [[] for _ in range(filas * columnas)]
    for i in range(enemigos):
        tipo = FICHAS[i % len(FICHAS)].id
        por_sala[azar.randrange(filas * columnas)].append(InstanciaEnemigo(f"e-{i:05d}", tipo))
    for indice, presentes in enumerate(por_sala):
        estado.cargar_contenido(ContenidoSala(indice + 1, tuple(presentes), (), ()))
    estado.iniciar()
    for enemigo in estado.enemigos_vivos():
        if not enemigo.activo:
            enemigo.activo = True
            estado.programar_accion(enemigo)
    return estado