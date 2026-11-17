"""Criptas mínimas para las pruebas de la segunda parte: salidas con costo, puertas
cerradas de un solo lado y salidas de un solo sentido."""
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.esqueleto import Esqueleto
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador


def salida(origen, direccion, destino, costo=None, cerrada=False, llave=None, cierre=None):
    return (origen, direccion, destino, costo, cerrada, llave, cierre)


def esqueleto(*salidas, salas=()):
    """Arma el esqueleto desde salidas(origen, dir, destino, costo, cerrada, llave).
    'salas' agrega salas sin salidas."""
    por_sala = {}
    for id_sala in salas:
        por_sala.setdefault(id_sala, {})
    for origen, direccion, destino, costo, cerrada, llave, cierre in salidas:
        datos = {"sala": destino}
        if cierre is not None:
            datos["cierre_automatico"] = cierre
        if costo is not None:
            datos["costo"] = costo
        if cerrada:
            datos["cerrada"] = True
            datos["llave"] = llave or "itm_llave"
        elif llave is not None:
            datos["llave"] = llave
        por_sala.setdefault(origen, {})[direccion] = datos
        por_sala.setdefault(destino, {})
    paginas = [{"id": i, "nombre": f"Sala {i}", "salidas": s} for i, s in sorted(por_sala.items())]
    e = Esqueleto()
    e.agregar_pagina(pagina_salas_desde_json({"pagina": 1, "total_paginas": 1, "salas": paginas}))
    return e


FICHAS = (
    FichaCatalogo(id="ent_sabueso", nombre="Sabueso", clase="enemigo", vida_max=1000, ataque=1,
                  defensa=0, velocidad=100, comportamiento="cazador", rango=600),
    FichaCatalogo(id="ent_espectro", nombre="Espectro", clase="enemigo", vida_max=1000, ataque=1,
                  defensa=0, velocidad=100, comportamiento="cazador", rango=2400),
    FichaCatalogo(id="ent_errante", nombre="Errante", clase="enemigo", vida_max=1000, ataque=1,
                  defensa=0, velocidad=100, comportamiento="errante"),
    FichaCatalogo(id="ent_rata", nombre="Rata", clase="enemigo", vida_max=1000, ataque=1,
                  defensa=0, velocidad=100, comportamiento="rastreador"),
    FichaCatalogo(id="ent_guardia", nombre="Guardia", clase="enemigo", vida_max=1000, ataque=1,
                  defensa=0, velocidad=100, comportamiento="guardián"),
    FichaCatalogo(id="itm_pocion", nombre="Poción", clase="pocion", peso=1, valor=5, cura=8),
    FichaCatalogo(id="itm_rapida", nombre="Poción rápida", clase="pocion", peso=1, valor=5,
                  modificador_velocidad=100, duracion=100),
    FichaCatalogo(id="itm_daga", nombre="Daga", clase="arma", peso=2, valor=15, ataque_bonus=3),
    FichaCatalogo(id="itm_antorcha", nombre="Antorcha", clase="antorcha", peso=1, valor=5,
                  duracion=200),
    FichaCatalogo(id="itm_llave", nombre="Llave", clase="llave", peso=1, valor=0),
    FichaCatalogo(id="itm_pergamino", nombre="Pergamino", clase="pergamino_retroceso", peso=0,
                  valor=0),
    FichaCatalogo(id="trp_pinchos", nombre="Pinchos", clase="trampa", dano=5, rearme=300),
)


def ficha(id_ficha):
    for f in FICHAS:
        if f.id == id_ficha:
            return f
    raise KeyError(id_ficha)


def partida(mapa, sala_jugador=1, velocidad=100, vida=1000, semilla=1, cargar=None,
            controlar_contenido=False, contenido=()):
    """Partida iniciada en t=0. 'contenido': ContenidoSala a cargar; 'cargar': salas
    con contenido vacío (por defecto todas las que no vienen en 'contenido')."""
    jugador = Jugador(sala_jugador, EstadisticasJugador(vida, 6, 2, velocidad), Inventario(10))
    estado = EstadoPartida(semilla, jugador, mapa, obtener_ficha=ficha)
    estado.controlar_contenido = controlar_contenido
    con_contenido = [c.sala for c in contenido]
    for c in contenido:
        estado.cargar_contenido(c)
    salas = cargar if cargar is not None else mapa.grafo().ids
    for id_sala in salas:
        if id_sala not in con_contenido:
            estado.cargar_contenido(ContenidoSala(id_sala, (), (), ()))
    estado.iniciar()
    return estado


def enemigo(estado, sala, tipo="ent_sabueso", instancia=None, activo=True):
    """Coloca un enemigo y, si está activo, programa su primera acción (costo 100)."""
    instancia = instancia or f"e-{len(estado.enemigos_vivos()) + 1}"
    nuevo = estado.colocar_enemigo(InstanciaEnemigo(instancia, tipo), ficha(tipo), sala)
    if activo:
        nuevo.activo = True
        estado.programar_accion(nuevo)
    return nuevo


def ronda(estado):
    """El jugador espera (100) y avanzan los demás hasta su turno."""
    estado.esperar()
    return estado.avanzar_hasta_turno_jugador()
