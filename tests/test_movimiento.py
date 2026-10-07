import unittest

from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.enemigo import Enemigo
from modelo.estado_partida import EstadoPartida
from modelo.evento import Evento
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.movimiento import (MovimientoInvalido, NO_ES_TURNO, PARTIDA_TERMINADA, PUERTA_ABIERTA,
                               PUERTA_CERRADA, SALA_NO_DISPONIBLE, SIN_LLAVE, SIN_MAPA, SIN_SALIDA)
from tests.test_actores import leer_json
from tests.test_esqueleto import esqueleto, esqueleto_cripta_01, sala


def llave(id_="itm_llave"):
    return FichaCatalogo(id=id_, nombre=id_, clase="llave", peso=1, valor=0)


def mapa_cruz():
    """La sala 1 en el centro: N->2, S->3, O->5 abiertas y E->4 con puerta cerrada (itm_llave)."""
    return esqueleto(sala(1, N=2, S=3, E=(4, True), O=5),
                     sala(2, S=1), sala(3, N=1), sala(4, O=1), sala(5, E=1))


def partida(mapa, sala=1, objetos=(), velocidad=100, vida=30, iniciar=True):
    inventario = Inventario(10)
    for objeto in objetos:
        inventario.recoger(objeto)
    jugador = Jugador(sala, EstadisticasJugador(vida, 6, 2, velocidad), inventario)
    estado = EstadoPartida(1, jugador, mapa)
    if iniciar:
        estado.iniciar()
    return estado


def ficha_rata(velocidad=150):
    return FichaCatalogo(id="ent_rata_gigante", nombre="Rata", clase="enemigo", vida_max=12,
                         ataque=5, defensa=1, velocidad=velocidad, comportamiento="rastreador")


class PruebasBase(unittest.TestCase):

    def assert_rechazada(self, estado, motivo, accion, direccion):
        """La acción se rechaza con ese motivo y no cambia nada: ni sala, ni turno, ni tiempo."""
        antes = (estado.jugador.sala, estado.jugador.proximo_evento,
                 estado.agenda.tamano(), estado.tiempo)
        with self.assertRaises(MovimientoInvalido) as ctx:
            accion(direccion)
        self.assertEqual(ctx.exception.motivo, motivo)
        despues = (estado.jugador.sala, estado.jugador.proximo_evento,
                   estado.agenda.tamano(), estado.tiempo)
        self.assertEqual(antes[0], despues[0])
        self.assertIs(antes[1], despues[1])
        self.assertEqual(antes[2:], despues[2:])


class PruebasMovimiento(PruebasBase):

    def test_mover_en_n_s_y_o_y_volver(self):
        for direccion, destino, vuelta in (("N", 2, "S"), ("S", 3, "N"), ("O", 5, "E")):
            estado = partida(mapa_cruz())
            self.assertEqual(estado.mover_jugador(direccion), destino)
            self.assertEqual(estado.jugador.sala, destino)
            estado.avanzar_hasta_turno_jugador()
            self.assertEqual(estado.mover_jugador(vuelta), 1)
            self.assertEqual(estado.jugador.sala, 1)

    def test_mover_cuesta_100_unidades_de_tiempo(self):
        estado = partida(mapa_cruz())
        self.assertEqual(estado.tiempo, 0)
        estado.mover_jugador("N")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 100)
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.tiempo, 100)
        estado.mover_jugador("S")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 200)

    def test_el_costo_se_escala_con_la_velocidad_del_jugador(self):
        estado = partida(mapa_cruz(), velocidad=200)
        estado.mover_jugador("N")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)

    def test_sin_conexion_en_esa_direccion(self):
        estado = partida(mapa_cruz(), sala=2)
        for direccion in ("N", "E", "O"):
            self.assert_rechazada(estado, SIN_SALIDA, estado.mover_jugador, direccion)

    def test_sala_destino_no_disponible(self):
        estado = partida(esqueleto(sala(1, N=9)))   # la sala 9 no esta en el mapa
        self.assert_rechazada(estado, SALA_NO_DISPONIBLE, estado.mover_jugador, "N")

    def test_sin_mapa(self):
        estado = partida(None)
        self.assert_rechazada(estado, SIN_MAPA, estado.mover_jugador, "N")

    def test_solo_se_mueve_en_su_turno(self):
        estado = partida(mapa_cruz(), iniciar=False)
        self.assert_rechazada(estado, NO_ES_TURNO, estado.mover_jugador, "N")
        estado.iniciar()
        estado.mover_jugador("N")
        # su siguiente turno es a las 100: no puede volver a actuar en este mismo momento
        estado.agenda.programar(50, Evento("accion", "e-999"))
        self.assertFalse(estado.es_turno_del_jugador())
        self.assert_rechazada(estado, NO_ES_TURNO, estado.mover_jugador, "S")

    def test_enemigo_que_actua_antes_del_siguiente_turno(self):
        estado = partida(mapa_cruz())
        estado.colocar_enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante"), ficha_rata(150), 2)
        estado.mover_jugador("N")                  # la rata se activa: su accion cae a las 66
        self.assertFalse(estado.es_turno_del_jugador())
        self.assert_rechazada(estado, NO_ES_TURNO, estado.mover_jugador, "S")
        resultados = estado.avanzar_hasta_turno_jugador()
        self.assertEqual(len(resultados), 1)
        self.assertEqual(estado.tiempo, 100)
        self.assertEqual(estado.mover_jugador("S"), 1)

    def test_jugador_muerto_no_se_mueve(self):
        estado = partida(mapa_cruz(), vida=1)
        estado.colocar_enemigo(InstanciaEnemigo("e-201", "ent_rata_gigante"), ficha_rata(150), 2)
        estado.mover_jugador("N")
        resultados = estado.avanzar_hasta_turno_jugador()
        self.assertTrue(resultados[-1].murio)
        self.assertIsNone(estado.jugador.proximo_evento)
        # con el jugador muerto la partida terminó
        self.assert_rechazada(estado, PARTIDA_TERMINADA, estado.mover_jugador, "S")
        with self.assertRaises(ValueError):
            estado.avanzar_hasta_turno_jugador()


class PruebasPuertas(PruebasBase):

    def test_puerta_cerrada_no_se_atraviesa(self):
        estado = partida(mapa_cruz(), objetos=[llave()])
        self.assert_rechazada(estado, PUERTA_CERRADA, estado.mover_jugador, "E")
        self.assertEqual(estado.jugador.sala, 1)

    def test_abrir_y_mover_son_acciones_separadas(self):
        estado = partida(mapa_cruz(), objetos=[llave()])
        puerta = estado.abrir_puerta("E")
        self.assertTrue(puerta.esta_abierta())
        self.assertEqual(estado.jugador.sala, 1)                       # abrir no mueve
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)   # abrir cuesta 50
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.mover_jugador("E"), 4)                 # ahora si
        self.assertEqual(estado.jugador.sala, 4)
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 150)
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.mover_jugador("O"), 1)

    def test_sin_la_llave_no_se_abre(self):
        estado = partida(mapa_cruz())
        self.assert_rechazada(estado, SIN_LLAVE, estado.abrir_puerta, "E")
        self.assertTrue(estado.esqueleto.puerta(1, "E").esta_cerrada())

    def test_otra_llave_no_abre(self):
        estado = partida(mapa_cruz(), objetos=[llave("itm_llave_bronce")])
        self.assert_rechazada(estado, SIN_LLAVE, estado.abrir_puerta, "E")
        self.assertTrue(estado.esqueleto.puerta(1, "E").esta_cerrada())

    def test_la_llave_no_se_consume_al_abrir(self):
        inventario_llave = llave()
        estado = partida(mapa_cruz(), objetos=[inventario_llave])
        inventario = estado.jugador.inventario
        estado.abrir_puerta("E")
        self.assertTrue(inventario.tiene_objeto_id("itm_llave"))
        self.assertEqual(len(inventario), 1)
        self.assertEqual(inventario.cantidad_de_clase("llave"), 1)
        # y sigue sirviendo: si la puerta se vuelve a cerrar, se abre otra vez
        estado.esqueleto.puerta(1, "E").cerrar()
        estado.avanzar_hasta_turno_jugador()
        estado.abrir_puerta("E")
        self.assertTrue(estado.esqueleto.puede_atravesar(1, "E"))
        self.assertEqual(len(inventario), 1)

    def test_volver_por_el_otro_lado_no_necesita_llave(self):
        estado = partida(mapa_cruz(), objetos=[llave()])
        estado.abrir_puerta("E")
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        estado.jugador.inventario.soltar_actual()            # ya no tiene la llave
        self.assertFalse(estado.jugador.inventario.tiene_objeto_id("itm_llave"))
        self.assertEqual(estado.mover_jugador("O"), 1)       # la salida O de la sala 4 ya estaba abierta
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.mover_jugador("E"), 4)

    def test_abrir_una_puerta_ya_abierta(self):
        estado = partida(mapa_cruz(), objetos=[llave()])
        self.assert_rechazada(estado, PUERTA_ABIERTA, estado.abrir_puerta, "N")

    def test_abrir_donde_no_hay_salida(self):
        estado = partida(mapa_cruz(), sala=2, objetos=[llave()])
        self.assert_rechazada(estado, SIN_SALIDA, estado.abrir_puerta, "E")

    def test_abrir_solo_en_su_turno(self):
        estado = partida(mapa_cruz(), objetos=[llave()], iniciar=False)
        self.assert_rechazada(estado, NO_ES_TURNO, estado.abrir_puerta, "E")

    def test_los_enemigos_no_abren_puertas(self):
        estado = partida(mapa_cruz(), objetos=[llave()])
        puerta = estado.esqueleto.puerta(1, "E")
        enemigo = Enemigo(InstanciaEnemigo("e-101", "ent_rata_gigante"), ficha_rata(), 1)
        self.assertFalse(hasattr(enemigo, "inventario"))
        self.assertFalse(enemigo.puede_abrir(puerta))
        self.assertTrue(estado.jugador.puede_abrir(puerta))
        self.assertFalse(partida(mapa_cruz()).jugador.puede_abrir(puerta))

    def test_recorrido_en_cripta_01_con_la_puerta_2_5(self):
        mapa = esqueleto_cripta_01()
        bronce = ficha_catalogo_desde_json(leer_json("catalogo", "fichas", "itm_llave_bronce.json"))
        estado = partida(mapa, sala=1)
        self.assertEqual(estado.mover_jugador("N"), 2)
        estado.avanzar_hasta_turno_jugador()
        self.assert_rechazada(estado, PUERTA_CERRADA, estado.mover_jugador, "E")
        self.assert_rechazada(estado, SIN_LLAVE, estado.abrir_puerta, "E")
        estado.jugador.inventario.recoger(bronce)
        estado.abrir_puerta("E")
        self.assertTrue(mapa.puede_atravesar(5, "O"))        # el lado de la sala 5 nunca estuvo cerrado
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.mover_jugador("E"), 5)
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.mover_jugador("O"), 2)
        self.assertTrue(estado.jugador.inventario.tiene_objeto_id("itm_llave_bronce"))
        # N, E y O cuestan 100 y abrir 50; los rechazos no gastaron tiempo
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 350)


if __name__ == "__main__":
    unittest.main()