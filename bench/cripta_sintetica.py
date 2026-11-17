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
# costos de las salidas sintéticas: los mismos valores que publica el API
COSTOS = (20, 50, 80, 100, 100, 100, 120, 150, 200, 300)


def ficha_cazador(rango, velocidad=110):
    return FichaCatalogo(id=f"ent_cazador_{rango}", nombre="Cazador", clase="enemigo",
                         vida_max=10 ** 6, ataque=1, defensa=0, velocidad=velocidad,
                         comportamiento="cazador", rango=rango)


def _buscar_ficha(fichas):
    def obtener(id_ficha):
        for ficha in fichas:
            if ficha.id == id_ficha:
                return ficha
        raise KeyError(id_ficha)
    return obtener


_ficha = _buscar_ficha(FICHAS)


def _sala(fila, columna, filas, columnas, costos=None):
    """costos: función (a, b) -> costo de la conexión entre las salas a y b, o None."""
    id_sala = fila * columnas + columna + 1
    vecinas = []
    if fila > 0:
        vecinas.append(("N", id_sala - columnas))
    if fila < filas - 1:
        vecinas.append(("S", id_sala + columnas))
    if columna < columnas - 1:
        vecinas.append(("E", id_sala + 1))
    if columna > 0:
        vecinas.append(("O", id_sala - 1))
    salidas = {}
    for direccion, destino in vecinas:
        salidas[direccion] = {"sala": destino}
        if costos is not None:
            salidas[direccion]["costo"] = costos(id_sala, destino)
    return {"id": id_sala, "nombre": f"S{id_sala}", "salidas": salidas}


def crear_esqueleto(filas, columnas, semilla=1, con_costos=False):
    """Cuadrícula de salas abiertas. Con costos, cada conexión cuesta lo mismo en los
    dos sentidos y se elige al azar (determinista por semilla)."""
    costos = None
    if con_costos:
        azar = random.Random(semilla * 7919)
        tabla = [[azar.choice(COSTOS) for _ in range(4)] for _ in range(filas * columnas)]

        def costos(a, b):
            menor, mayor = (a, b) if a < b else (b, a)
            return tabla[menor - 1][0 if mayor == menor + 1 else 1]
    salas = [_sala(f, c, filas, columnas, costos) for f in range(filas) for c in range(columnas)]
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina(pagina_salas_desde_json(
        {"pagina": 1, "total_paginas": 1, "salas": salas}))
    return esqueleto


def crear_partida(filas, columnas, enemigos, semilla=1, cazadores=0, rango=600,
                  con_costos=False):
    """Cuadrícula de salas abiertas con muchos enemigos ya activos: para medir el
    motor sin red ni vista. El jugador empieza en el centro y casi no recibe daño.
    'cazadores' de esos enemigos son cazadores con ese rango."""
    esqueleto = crear_esqueleto(filas, columnas, semilla, con_costos)
    centro = (filas // 2) * columnas + columnas // 2 + 1
    jugador = Jugador(centro, EstadisticasJugador(10 ** 9, 5, 10 ** 6, 100), Inventario(10))
    cazador = ficha_cazador(rango)
    estado = EstadoPartida(semilla, jugador, esqueleto,
                           obtener_ficha=_buscar_ficha(FICHAS + (cazador,)))
    azar = random.Random(semilla)
    por_sala = [[] for _ in range(filas * columnas)]
    for i in range(enemigos):
        tipo = cazador.id if i < cazadores else FICHAS[i % len(FICHAS)].id
        por_sala[azar.randrange(filas * columnas)].append(InstanciaEnemigo(f"e-{i:05d}", tipo))
    for indice, presentes in enumerate(por_sala):
        estado.cargar_contenido(ContenidoSala(indice + 1, tuple(presentes), (), ()))
    estado.iniciar()
    for enemigo in estado.enemigos_vivos():
        if not enemigo.activo:
            enemigo.activo = True
            estado.programar_accion(enemigo)
    return estado