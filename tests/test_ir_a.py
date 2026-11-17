import os
import tempfile
import unittest

from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.mapa_conocido import CERRADA
from tests.criptas_prueba import ficha, salida
from tests.fuente_memoria import controlador, trampa


def ida_y_vuelta(a, direccion, b, costo=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, costo), salida(b, contraria, a, costo)]


def linea(*salas, direccion="E", costo=None):
    salidas = []
    for a, b in zip(salas, salas[1:]):
        salidas += ida_y_vuelta(a, direccion, b, costo)
    return salidas


class ConBitacora(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def jugar(self, c, comandos):
        """Juega con el bucle real del controlador y devuelve las líneas de la bitácora."""
        ruta = os.path.join(self.carpeta.name, "p.log")
        bitacora = BitacoraPartida(ruta)
        bitacora.crear(CabeceraPartida("prueba", "v1", "c1", 1))
        pendientes = iter(comandos)
        c.jugar(lambda: next(pendientes, None), bitacora)
        with open(ruta, encoding="utf-8") as archivo:
            lineas = [l.rstrip("\n") for l in archivo]
        return lineas[lineas.index("---") + 1:], ruta

    def pasos(self, c):
        return c.ultimo_viaje


class PruebasIrA(ConBitacora):

    def test_destino_no_explorado_se_rechaza(self):
        # FR-109 (Apéndice B): no consume tiempo ni cuenta como acción
        c = controlador(linea(1, 2, 3))
        for orden in ("ir a 3", "ir a 1", "ir a 99", "ir a tres", "ir a"):
            antes = (c.estado.tiempo, c.estado.acciones, c.estado.jugador.sala)
            c.ejecutar(orden)
            self.assertEqual((c.estado.tiempo, c.estado.acciones, c.estado.jugador.sala), antes)
            self.assertTrue(c.bitacora.ultimos()[-1].startswith("No se puede"), orden)
        self.assertIn("no está explorada", c.bitacora.ultimos()[-5])

    def test_llega_al_destino(self):
        # FR-108: cada paso es un movimiento ordinario con su costo y sus eventos
        c = controlador(linea(1, 2, 3, 4, costo=60))
        for _ in range(3):
            c.ejecutar("e")
        c.ejecutar("ir a 1")
        self.assertEqual(c.estado.jugador.sala, 1)
        self.assertEqual(c.ultimo_viaje[1], 3)
        self.assertIn("llegaste", c.ultimo_viaje[2])
        self.assertEqual(c.estado.acciones, 6)
        self.assertEqual(c.estado.tiempo, 6 * 60)

    def test_ruta_mas_barata_y_desempate(self):
        # FR-110: de 1 a 4 directo cuesta 400; por 2-3, 300; por 5-6 también 300.
        # Gana la de menor costo y, entre las dos de 300, la que empieza por la vecina 2
        salidas = (ida_y_vuelta(1, "E", 4, 400) + ida_y_vuelta(1, "N", 5, 100)
                   + ida_y_vuelta(5, "E", 6, 100) + ida_y_vuelta(6, "S", 4, 100)
                   + ida_y_vuelta(1, "S", 2, 100) + ida_y_vuelta(2, "E", 3, 100)
                   + ida_y_vuelta(3, "N", 4, 100))
        c = controlador(salidas)
        for orden in ("n", "e", "s", "o", "s", "e", "n", "o"):   # explora todo y vuelve a 1
            c.ejecutar(orden)
        self.assertEqual(c.estado.jugador.sala, 1)
        lineas, _ = self.jugar(c, ["ir a 4"])
        self.assertEqual(lineas, ["# ir a 4", "s", "e", "n"])

    def test_puerta_recordada_abierta_esta_cerrada(self):
        # FR-103, FR-111, FR-112 (Apéndice B): la puerta 2->3 se cerró sola sin que el
        # jugador la viera. «ir a 3» va primero hacia 2, ahí la ve cerrada y recalcula.
        salidas = (ida_y_vuelta(1, "N", 2) + [salida(2, "E", 3, cerrada=True, cierre=200),
                                               salida(3, "O", 2)]
                   + ida_y_vuelta(3, "S", 5, 50) + ida_y_vuelta(5, "O", 4) + ida_y_vuelta(4, "N", 1))
        c = controlador(salidas)
        c.estado.jugador.inventario.recoger(ficha("itm_llave"))
        for orden in ("n", "abrir e", "e", "s", "o", "n"):
            c.ejecutar(orden)
        self.assertEqual(c.estado.jugador.sala, 1)
        puerta = c.esqueleto.puerta(2, "E")
        self.assertTrue(puerta.esta_cerrada())
        self.assertNotEqual(c.estado.mapa.recuerdo_de(puerta.indice), CERRADA)
        lineas, _ = self.jugar(c, ["ir a 3"])
        self.assertEqual(lineas, ["# ir a 3", "n", "s", "s", "e", "n"])
        self.assertEqual(c.estado.jugador.sala, 3)
        self.assertEqual(c.estado.mapa.recuerdo_de(puerta.indice), CERRADA)

    def test_sin_ruta_tras_observar_se_detiene_sin_tiempo_extra(self):
        # FR-112 (Apéndice B): igual que el anterior, pero sin camino alternativo
        salidas = (ida_y_vuelta(1, "N", 2) + [salida(2, "E", 3, cerrada=True, cierre=200),
                                               salida(3, "O", 2)]
                   + [salida(3, "S", 5, 50), salida(5, "O", 1)])
        c = controlador(salidas)
        c.estado.jugador.inventario.recoger(ficha("itm_llave"))
        for orden in ("n", "abrir e", "e", "s", "o"):
            c.ejecutar(orden)
        self.assertEqual(c.estado.jugador.sala, 1)
        c.ejecutar("ir a 3")
        self.assertEqual(c.estado.jugador.sala, 2)
        self.assertEqual(c.ultimo_viaje[1], 1)
        self.assertIn("no queda una ruta", c.ultimo_viaje[2])
        # el reloj quedó en el turno del jugador después del único paso
        self.assertEqual(c.estado.tiempo, c.estado.jugador.proximo_evento.tiempo_siguiente)

    def test_enemigos_dormidos_detienen_y_se_activan(self):
        # FR-112 (Apéndice B): con la antorcha se exploró 2 sin despertar al guardia;
        # el viaje a 3 pasa por 2, lo despierta y se detiene ahí
        salidas = (ida_y_vuelta(1, "N", 5) + ida_y_vuelta(5, "E", 2, 100)
                   + ida_y_vuelta(5, "S", 3, 500) + ida_y_vuelta(2, "S", 3, 100))
        guardia = ContenidoSala(2, (InstanciaEnemigo("g-1", "ent_guardia"),), (), ())
        c = controlador(salidas, contenidos=[guardia])
        c.estado.jugador.inventario.recoger(ficha("itm_antorcha"))
        c.ejecutar("usar")
        c.ejecutar("n")
        self.assertFalse(c.estado.enemigo("g-1").activo)
        c.ejecutar("ir a 3")
        self.assertEqual(c.estado.jugador.sala, 2)
        self.assertTrue(c.estado.enemigo("g-1").activo)
        self.assertIn("enemigos", c.ultimo_viaje[2])

    def test_dano_detiene(self):
        # FR-112: una trampa armada en el camino hace daño y el viaje se detiene ahí
        salidas = (ida_y_vuelta(1, "N", 5) + ida_y_vuelta(5, "E", 2, 100)
                   + ida_y_vuelta(5, "S", 3, 500) + ida_y_vuelta(2, "S", 3, 100))
        c = controlador(salidas, contenidos=[trampa(2)])
        c.estado.jugador.inventario.recoger(ficha("itm_antorcha"))
        c.ejecutar("usar")
        c.ejecutar("n")
        vida = c.estado.jugador.vida
        c.ejecutar("ir a 3")
        self.assertEqual(c.estado.jugador.sala, 2)
        self.assertLess(c.estado.jugador.vida, vida)
        self.assertIn("daño", c.ultimo_viaje[2])

    def test_pergamino_durante_viaje(self):
        # FR-114 (Apéndice B): el pergamino revierte solo el último paso y no sigue
        c = controlador(linea(1, 2, 3, 4))
        for _ in range(3):
            c.ejecutar("e")
        c.estado.jugador.inventario.recoger(ficha("itm_pergamino"))
        c.ejecutar("ir a 1")
        acciones = c.estado.acciones
        tiempo_antes_del_ultimo = c.estado.tiempo - 100
        c.ejecutar("deshacer")
        self.assertEqual(c.estado.jugador.sala, 2)
        self.assertEqual(c.estado.acciones, acciones - 1)
        self.assertEqual(c.estado.tiempo, tiempo_antes_del_ultimo)

    def test_no_abre_puertas(self):
        # FR-111, FR-112: la única ruta conocida tiene una puerta cerrada; hay llave y no se usa
        salidas = [salida(1, "E", 2, cerrada=True), salida(2, "O", 1)] + linea(1, 3, direccion="N")
        c = controlador(salidas)
        c.estado.jugador.inventario.recoger(ficha("itm_llave"))
        c.estado.antorcha_hasta = 10 ** 6        # para explorar la 2 sin abrir la puerta
        c.ejecutar("n")
        c.ejecutar("s")
        antes = (c.estado.tiempo, c.estado.acciones)
        c.ejecutar("ir a 2")
        self.assertEqual((c.estado.tiempo, c.estado.acciones), antes)
        self.assertIn("no queda una ruta", c.ultimo_viaje[2])
        self.assertTrue(c.esqueleto.puerta(1, "E").esta_cerrada())


class PruebasBitacoraDelViaje(ConBitacora):

    def test_bitacora_pasos_y_comentario_y_replay(self):
        # FR-113, SC-103: los pasos son movimientos, la orden un comentario, y el replay
        # (que ignora los comentarios) llega exactamente al mismo estado
        c = controlador(linea(1, 2, 3, 4, costo=70))
        lineas, ruta = self.jugar(c, ["e", "e", "e", "ir a 1", "esperar"])
        self.assertEqual(lineas, ["e", "e", "e", "# ir a 1", "o", "o", "o", "esperar"])
        _, comandos = BitacoraPartida.leer(ruta)
        self.assertEqual(comandos, ["e", "e", "e", "o", "o", "o", "esperar"])
        otro = controlador(linea(1, 2, 3, 4, costo=70))
        pendientes = iter(comandos)
        otro.jugar(lambda: next(pendientes, None))
        for estado in (c.estado, otro.estado):
            self.assertEqual(estado.jugador.sala, 1)
        self.assertEqual((c.estado.tiempo, c.estado.acciones, c.estado.mapa.estado),
                         (otro.estado.tiempo, otro.estado.acciones, otro.estado.mapa.estado))


if __name__ == "__main__":
    unittest.main()
