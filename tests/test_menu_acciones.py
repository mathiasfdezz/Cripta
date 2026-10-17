import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

import main
from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.rutas_offline import RutasOffline
from controlador.partida import ControladorPartida
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.cache_catalogo import CacheCatalogo
from tests.test_acciones import ficha, partida
from tests.test_partida import CARPETA_OFFLINE
from vista.consola import Consola
from vista.menu_acciones import MenuAcciones


def comandos(opciones, texto):
    for etiqueta, _, pasos in opciones:
        if texto in etiqueta:
            return pasos
    raise AssertionError(f"no hay una opción con '{texto}': {[o[0] for o in opciones]}")


class PruebasMenuAcciones(unittest.TestCase):

    def test_solo_ofrece_lo_que_se_puede_hacer(self):
        estado = partida(objetos=["itm_daga"], enemigos=[InstanciaEnemigo("e-1", "ent_rata")])
        opciones = MenuAcciones().armar(estado, estado.esqueleto)
        textos = [o[0] for o in opciones]
        self.assertEqual(comandos(opciones, "Ir al Norte"), ("n",))
        self.assertEqual(comandos(opciones, "Atacar a Rata e-1"), ("atacar e-1",))
        self.assertEqual(comandos(opciones, "Recoger daga"), ("recoger itm_daga",))
        self.assertIn("Esperar (dejar pasar el turno)", textos)
        # sin pergaminos no se ofrece deshacer, y no hay salidas al sur
        self.assertFalse(any("pergamino" in t for t in textos))
        self.assertFalse(any("Sur" in t for t in textos))

    def test_usar_y_equipar_mueven_el_cursor_lo_justo(self):
        estado = partida()
        inventario = estado.jugador.inventario
        for id_objeto in ("itm_daga", "itm_pocion", "itm_rapida"):
            inventario.recoger(ficha(id_objeto))
        menu = MenuAcciones()
        opciones = menu.armar(estado, estado.esqueleto)
        self.assertEqual(comandos(opciones, "Equipar Daga"), ("equipar",))
        self.assertEqual(comandos(opciones, "Usar Poción (cura 8)"), ("sig", "usar"))
        self.assertEqual(comandos(opciones, "Usar Poción rápida"), ("sig", "sig", "usar"))
        inventario.avanzar()
        inventario.avanzar()
        opciones = menu.armar(estado, estado.esqueleto)
        self.assertEqual(comandos(opciones, "Equipar Daga"), ("ant", "ant", "equipar"))

    def test_puerta_cerrada_solo_si_tienes_la_llave(self):
        estado = partida(cargar=(1, 2, 3))
        estado.mover_jugador("N")
        estado.avanzar_hasta_turno_jugador()
        menu = MenuAcciones()
        self.assertFalse(any("Abrir" in o[0] for o in menu.armar(estado, estado.esqueleto)))
        estado.jugador.inventario.recoger(ficha("itm_llave"))
        self.assertEqual(comandos(menu.armar(estado, estado.esqueleto), "Abrir la puerta del Este"),
                         ("abrir e",))

    def test_inventario_lleno_ofrece_soltar_y_no_recoger(self):
        estado = partida(objetos=["itm_daga"], capacidad=1)
        estado.jugador.inventario.recoger(ficha("itm_pocion"))
        textos = [o[0] for o in MenuAcciones().armar(estado, estado.esqueleto)]
        self.assertFalse(any(t.startswith("Recoger") for t in textos))
        self.assertTrue(any(t.startswith("Soltar Poción") for t in textos))


class PruebasConsolaConMenu(unittest.TestCase):

    def setUp(self):
        self.consola = Consola()
        self.estado = partida(objetos=["itm_daga"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.consola.mostrar_partida(self.estado, self.estado.esqueleto, [])

    def test_un_numero_valido_entrega_los_comandos_de_a_uno(self):
        self.estado.jugador.inventario.recoger(ficha("itm_pocion"))
        self.estado.jugador.inventario.recoger(ficha("itm_rapida"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.consola.mostrar_partida(self.estado, self.estado.esqueleto, [])
        numero = [o[0] for o in self.consola._opciones].index("Usar Poción rápida "
                                                              "(velocidad +100 durante 300)") + 1
        # el cursor está en la poción y la rápida es la siguiente: un 'sig' y 'usar'
        with patch("builtins.input", return_value=str(numero)) as entrada:
            entregados = [self.consola.pedir_comando() for _ in range(2)]
        self.assertEqual(entregados, ["sig", "usar"])
        self.assertEqual(entrada.call_count, 1)        # el segundo no volvió a preguntar
        self.assertEqual(self.consola._pendientes, [])

    def test_si_un_paso_se_rechaza_se_cancela_el_resto(self):
        self.consola._pendientes = ["sig", "usar"]
        self.consola.mostrar_resultado("sig", ["No se puede: algo."])
        self.assertEqual(self.consola._pendientes, [])

    def test_un_numero_que_no_existe_no_llega_al_juego(self):
        with patch("builtins.input", return_value="99"), \
                contextlib.redirect_stdout(io.StringIO()) as salida:
            self.assertEqual(self.consola.pedir_comando(), "")
        self.assertIn("No hay una opción 99", salida.getvalue())

    def test_ctrl_c_termina_ordenado_y_fin_de_entrada_devuelve_none(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with patch("builtins.input", side_effect=KeyboardInterrupt):
                self.assertEqual(self.consola.pedir_comando(), "salir")
            with patch("builtins.input", side_effect=EOFError):
                self.assertIsNone(self.consola.pedir_comando())


class PruebasPartidaConElMenu(unittest.TestCase):
    """Partidas completas en las criptas del paquete offline eligiendo opciones por número."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def jugar_eligiendo(self, cripta, elecciones):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta(cripta)
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "c")))
        version = fuente.version_catalogo()
        cache.validar_version(version)
        consola = Consola()
        controlador = ControladorPartida(datos, fuente, cache, consola, 7, version,
                                         os.path.join(self.carpeta.name, "p"))
        ruta = os.path.join(self.carpeta.name, "p.log")
        bitacora = BitacoraPartida(ruta)
        bitacora.crear(CabeceraPartida(datos.id, datos.version, version, 7))
        pendientes = iter(elecciones)

        def responder(_pregunta=""):
            # se elige por el texto de la opción, buscando su número en el menú actual
            texto = next(pendientes, None)
            if texto is None:
                raise EOFError
            return str([o[0] for o in consola._opciones].index(
                next(o[0] for o in consola._opciones if texto in o[0])) + 1)

        with patch("builtins.input", responder), contextlib.redirect_stdout(io.StringIO()):
            controlador.jugar(consola.pedir_comando, bitacora)
        return controlador.estado, BitacoraPartida.leer(ruta)[1]

    def test_recoger_moverse_y_equipar_con_numeros(self):
        estado, guardados = self.jugar_eligiendo(
            "cripta-02", ["Recoger antorcha", "Ir al Norte", "Recoger daga", "Equipar Daga"])
        self.assertEqual(estado.jugador.sala, 2)
        self.assertEqual(estado.jugador.inventario.arma_equipada().id, "itm_daga_oxidada")
        # la bitácora tiene los comandos reales, no los números del menú
        self.assertEqual(guardados, ["recoger itm_antorcha", "n", "recoger itm_daga_oxidada",
                                     "sig", "equipar"])

    def test_main_arranca_y_sale_con_q(self):
        salida = io.StringIO()
        main.CARPETA_PARTIDAS = os.path.join(self.carpeta.name, "partidas")
        with patch("builtins.input", side_effect=["q"]), contextlib.redirect_stdout(salida):
            codigo = main.principal(["cripta-02", "--offline", "--semilla", "1"])
        self.assertEqual(codigo, 0)
        self.assertIn("¿Qué haces?", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
