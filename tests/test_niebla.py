import os
import tempfile
import unittest

from adaptadores.guardado_binario import MAGIC, GuardadoIncompatible
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.instancia_trampa import InstanciaTrampa
from modelo.mapa_conocido import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, SIN_OBSERVAR
from tests.criptas_prueba import esqueleto, ficha, partida, salida
from tests.fuente_memoria import controlador


def estados(estado, *salas):
    return [estado.mapa.estado_de(s) for s in salas]


def ida_y_vuelta(a, direccion, b, costo=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, costo), salida(b, contraria, a, costo)]


class PruebasExploracion(unittest.TestCase):

    def test_estado_inicial(self):
        # FR-101, FR-102: la inicial explorada desde t=0, sus destinos avistados, el resto nada
        mapa = esqueleto(*ida_y_vuelta(1, "N", 2), *ida_y_vuelta(2, "N", 3), salida(1, "E", 4))
        estado = partida(mapa)
        self.assertEqual(estados(estado, 1, 2, 4, 3), [EXPLORADA, AVISTADA, AVISTADA, DESCONOCIDA])
        self.assertEqual(estado.mapa.salas_exploradas(), [1])
        self.assertEqual(estado.mapa.salas_avistadas(), [2, 4])

    def test_entrar_explora_y_aviste(self):
        # FR-101, FR-102
        mapa = esqueleto(*ida_y_vuelta(1, "N", 2), *ida_y_vuelta(2, "N", 3), salida(1, "E", 4))
        estado = partida(mapa)
        estado.mover_jugador("N")
        self.assertEqual(estados(estado, 1, 2, 3, 4), [EXPLORADA, EXPLORADA, AVISTADA, AVISTADA])

    def test_avistada_tras_puerta_cerrada_sigue_avistada(self):
        # FR-102: una sala a la que solo se llega por una salida cerrada queda avistada
        estado = partida(esqueleto(salida(1, "N", 2, cerrada=True), salida(2, "S", 1)))
        self.assertEqual(estado.mapa.estado_de(2), AVISTADA)


class PruebasMemoriaDePuertas(unittest.TestCase):

    def test_mapa_recuerda_puerta_vieja(self):
        # FR-103: la puerta 2->3 se cierra sola con el jugador lejos; el mapa la recuerda abierta
        salidas = (ida_y_vuelta(1, "N", 2) + [salida(2, "E", 3, cerrada=True, cierre=200),
                                               salida(3, "O", 2)] + ida_y_vuelta(3, "S", 5, 50))
        estado = partida(esqueleto(*salidas))
        estado.jugador.inventario.recoger(ficha("itm_llave"))
        puerta = estado.esqueleto.puerta(2, "E")
        estado.mover_jugador("N")                     # t=0  -> llega a 2, turno en 100
        estado.avanzar_hasta_turno_jugador()
        estado.abrir_puerta("E")                      # t=100, se cierra sola en t=300
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("E")                     # t=150 -> en 3, turno en 250
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("S")                     # t=250 -> en 5, turno en 300
        estado.avanzar_hasta_turno_jugador()          # en t=300 se cierra lejos del jugador
        self.assertTrue(puerta.esta_cerrada())
        self.assertEqual(estado.mapa.recuerdo_de(puerta.indice), ABIERTA)
        # al volver a una de las dos salas que une, se observa
        estado.mover_jugador("N")
        self.assertEqual(estado.mapa.recuerdo_de(puerta.indice), CERRADA)

    def test_observa_salidas_que_llegan(self):
        # FR-103: estando en 2 se ve la salida 3->2 aunque la 3 no esté explorada, y cada
        # salida de un solo sentido o cerrada de un solo lado se recuerda por separado
        mapa = esqueleto(*ida_y_vuelta(1, "N", 2), salida(3, "O", 2, cerrada=True),
                         salida(2, "E", 3))
        estado = partida(mapa)
        entrante = mapa.puerta(3, "O")
        self.assertEqual(estado.mapa.recuerdo_de(entrante.indice), SIN_OBSERVAR)
        estado.mover_jugador("N")
        self.assertEqual(estado.mapa.recuerdo_de(entrante.indice), CERRADA)
        self.assertEqual(estado.mapa.recuerdo_de(mapa.puerta(2, "E").indice), ABIERTA)
        self.assertEqual(estado.mapa.estado_de(3), AVISTADA)


def con_antorcha():
    """1 -E- 2; desde 2 salen cuatro vecinas: 3 (cerrada), 4, 5 y 6. En 3 duerme un
    guardia y en 4 hay una trampa armada."""
    salidas = (ida_y_vuelta(1, "E", 2) + [salida(2, "N", 3, cerrada=True), salida(3, "S", 2)]
               + ida_y_vuelta(2, "S", 4) + ida_y_vuelta(2, "E", 5) + [salida(5, "N", 6)])
    contenidos = [ContenidoSala(3, (InstanciaEnemigo("g-1", "ent_guardia"),), (), ()),
                  ContenidoSala(4, (), ("itm_daga",), (InstanciaTrampa("t-1", "trp_pinchos"),))]
    estado = partida(esqueleto(*salidas), contenido=contenidos)
    inventario = estado.jugador.inventario
    inventario.recoger(ficha("itm_antorcha"))
    inventario.recoger(ficha("itm_pergamino"))
    estado.usar()                                    # la antorcha: queda encendida 200
    estado.avanzar_hasta_turno_jugador()
    return estado


class PruebasAntorcha(unittest.TestCase):

    def test_antorcha_explora_vecinas_sin_activar(self):
        # FR-104 (Apéndice B): entrar a 2 con la antorcha explora 3, 4 y 5 por cualquier
        # salida (3 tiene la puerta cerrada); 6 queda avistada
        estado = con_antorcha()
        vida = estado.jugador.vida
        estado.mover_jugador("E")
        self.assertEqual(estados(estado, 2, 3, 4, 5, 6),
                         [EXPLORADA, EXPLORADA, EXPLORADA, EXPLORADA, AVISTADA])
        self.assertFalse(estado.enemigo("g-1").activo)
        self.assertTrue(estado.trampas_en(4)[0].armada)
        self.assertEqual(estado.jugador.vida, vida)
        # explorar no lleva al jugador ni toca el contenido
        self.assertEqual(estado.suelo(4), ["itm_daga"])
        self.assertEqual(estado.jugador.sala, 2)

    def test_sin_antorcha_no_explora_vecinas(self):
        estado = con_antorcha()
        estado.antorcha_hasta = None
        estado.mover_jugador("E")
        self.assertEqual(estados(estado, 3, 4, 5), [AVISTADA, AVISTADA, AVISTADA])

    def test_pergamino_revierte_exploracion_con_antorcha(self):
        # FR-106 (Apéndice B): la entrada exploró cinco salas (2 y sus cuatro vecinas
        # contando la 1 ya explorada) y avistó la 6; el pergamino deja el mapa como antes
        estado = con_antorcha()
        antes = (list(estado.mapa.estado), list(estado.mapa.recuerdo))
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        self.assertNotEqual(antes[0], estado.mapa.estado)
        estado.deshacer()
        self.assertEqual((estado.mapa.estado, estado.mapa.recuerdo), antes)
        self.assertEqual(estado.jugador.sala, 1)


class PruebasGuardado(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def test_guardar_y_cargar_conserva_el_mapa(self):
        # FR-106
        salidas = ida_y_vuelta(1, "N", 2) + ida_y_vuelta(2, "N", 3) + ida_y_vuelta(3, "E", 4)
        c = controlador(salidas, carpeta=self.carpeta.name)
        for comando in ("n", "n"):
            c.ejecutar(comando)
        antes = (list(c.estado.mapa.estado), list(c.estado.mapa.recuerdo))
        c.ejecutar("guardar prueba")
        c.ejecutar("s")
        c.ejecutar("cargar prueba")
        self.assertEqual((c.estado.mapa.estado, c.estado.mapa.recuerdo), antes)
        self.assertEqual(c.estado.jugador.sala, 3)
        # el mapa cargado sigue anotando en el historial de la partida cargada
        c.ejecutar("e")
        self.assertEqual(c.estado.mapa.estado_de(4), EXPLORADA)

    def test_guardado_version_anterior_incompatible(self):
        # FR-106: un archivo con otra versión de formato se rechaza y se avisa
        c = controlador(ida_y_vuelta(1, "N", 2), carpeta=self.carpeta.name)
        c.ejecutar("guardar viejo")
        ruta = os.path.join(self.carpeta.name, "viejo.sav")
        with open(ruta, "rb") as archivo:
            crudo = bytearray(archivo.read())
        self.assertEqual(bytes(crudo[:4]), MAGIC)
        crudo[4:6] = (3).to_bytes(2, "little")
        with open(ruta, "wb") as archivo:
            archivo.write(bytes(crudo))
        from adaptadores.guardado_partida import GuardadoPartida
        with self.assertRaises(GuardadoIncompatible) as ctx:
            GuardadoPartida.cargar(ruta, c.datos, "c1", c.esqueleto, c.cache.obtener)
        self.assertIn("version 3", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
