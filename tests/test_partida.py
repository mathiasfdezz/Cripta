import os
import tempfile
import unittest

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.error_bitacora import ErrorBitacora
from adaptadores.rutas_offline import RutasOffline
from adaptadores.tabla_puntajes import TablaPuntajes
from controlador.partida import ControladorPartida
from modelo.cache_catalogo import CacheCatalogo
from modelo.registro_puntaje import RegistroPuntaje

CARPETA_OFFLINE = os.path.join(os.path.dirname(__file__), "..", "datos_offline")


class VistaMuda:
    """Vista de prueba: no imprime ni pide nada, solo anota lo que le llega."""

    def __init__(self):
        self.mensajes = []

    def mostrar_partida(self, estado, esqueleto, mensajes):
        pass

    def mostrar_resultado(self, comando, mensajes):
        self.mensajes.extend(mensajes)

    def mostrar_objeto_actual(self, objeto):
        pass

    def mostrar_inventario_detallado(self, pares):
        self.inventario = pares

    def mostrar_ayuda(self):
        pass

    def mostrar_fin(self, estado):
        pass


class PruebasPartida(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def nueva(self, semilla=3):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta("cripta-01")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "cache")))
        cache.validar_version(fuente.version_catalogo())
        return ControladorPartida(datos, fuente, cache, VistaMuda(), semilla)

    def jugar(self, controlador, comandos):
        pendientes = iter(comandos)
        controlador.jugar(lambda: next(pendientes, None))
        return controlador.estado

    def test_arranca_en_la_sala_inicial_con_su_contenido(self):
        controlador = self.nueva()
        self.assertEqual(controlador.estado.jugador.sala, 1)
        self.assertEqual(controlador.estado.suelo(1), ["itm_antorcha"])
        self.assertTrue(controlador.estado.es_turno_del_jugador())

    def test_un_recorrido_cambia_de_sala_y_gasta_tiempo(self):
        estado = self.jugar(self.nueva(), ["recoger", "n"])
        self.assertEqual(estado.jugador.sala, 2)
        self.assertEqual(estado.jugador.inventario.obtener_actual().id, "itm_antorcha")
        self.assertGreater(estado.tiempo, 0)

    def test_un_comando_invalido_no_rompe_la_partida(self):
        controlador = self.nueva()
        estado = self.jugar(controlador, ["volar", "abrir n", "atacar", "o", "e"])
        self.assertEqual((estado.jugador.sala, estado.tiempo), (1, 0))
        self.assertTrue(any("No se puede" in m for m in controlador.vista.mensajes))

    def test_misma_semilla_y_comandos_dan_la_misma_partida(self):
        comandos = ["n", "recoger", "equipar", "atacar e-201", "atacar e-201", "atacar e-202"]
        a = self.jugar(self.nueva(semilla=11), comandos)
        b = self.jugar(self.nueva(semilla=11), comandos)
        self.assertEqual((a.tiempo, a.jugador.vida, a.resultado, a.enemigos_derrotados),
                         (b.tiempo, b.jugador.vida, b.resultado, b.enemigos_derrotados))

    def test_inventario_ordenado_por_valor(self):
        controlador = self.nueva()
        self.jugar(controlador, ["recoger", "inv valor"])
        self.assertEqual([o.id for o, _ in controlador.vista.inventario], ["itm_antorcha"])

    def test_salir_termina_sin_resultado(self):
        estado = self.jugar(self.nueva(), ["n", "salir", "s"])
        self.assertEqual(estado.jugador.sala, 2)        # lo que venía después de salir no corre
        self.assertFalse(estado.terminada())


class PruebasBitacoraPartida(unittest.TestCase):

    def test_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "p.log")
            bitacora = BitacoraPartida(ruta)
            bitacora.crear(CabeceraPartida("cripta-01", "v1", "cat-1", 42))
            bitacora.anotar("n")
            bitacora.anotar("atacar e-201")
            cabecera, comandos = BitacoraPartida.leer(ruta)
        self.assertEqual(cabecera, CabeceraPartida("cripta-01", "v1", "cat-1", 42))
        self.assertEqual(comandos, ["n", "atacar e-201"])

    def test_archivo_que_no_es_bitacora(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "otro.log")
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write("hola\n")
            with self.assertRaises(ErrorBitacora):
                BitacoraPartida.leer(ruta)
            with self.assertRaises(ErrorBitacora):
                BitacoraPartida.leer(os.path.join(carpeta, "no-existe.log"))


class PruebasTablaPuntajes(unittest.TestCase):

    def test_victorias_primero_y_luego_menos_acciones(self):
        with tempfile.TemporaryDirectory() as carpeta:
            tabla = TablaPuntajes(os.path.join(carpeta, "puntajes.txt"))
            tabla.agregar(RegistroPuntaje("Ana", "cripta-01", "v1", "derrota", 5, 0, 300))
            tabla.agregar(RegistroPuntaje("Beto", "cripta-01", "v1", "victoria", 40, 2, 4000))
            tabla.agregar(RegistroPuntaje("Caro", "cripta-01", "v1", "victoria", 30, 1, 3500))
            self.assertEqual([r.nombre for r in tabla.leer()], ["Caro", "Beto", "Ana"])

    def test_sin_archivo_esta_vacia(self):
        with tempfile.TemporaryDirectory() as carpeta:
            self.assertEqual(TablaPuntajes(os.path.join(carpeta, "x.txt")).leer(), [])


if __name__ == "__main__":
    unittest.main()
