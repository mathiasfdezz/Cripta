import os
import tempfile
import unittest

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.guardado_binario import ArchivoGuardado, GuardadoIncompatible
from adaptadores.guardado_partida import GuardadoPartida
from adaptadores.rutas_offline import RutasOffline
from controlador.partida import ControladorPartida
from modelo.cache_catalogo import CacheCatalogo
from tests.test_partida import CARPETA_OFFLINE, VistaMuda


def foto(estado):
    """Lo observable de la partida, para comparar."""
    enemigos = [(e.id, e.vida, e.sala, e.activo,
                 None if e.proximo_evento is None else e.proximo_evento.tiempo_siguiente)
                for e in estado.enemigos_vivos()]
    inventario = estado.jugador.inventario
    agenda = sorted((t, s, e.tipo, e.objetivo) for t, s, e in estado.agenda.pendientes())
    return (estado.tiempo, estado.jugador.vida, estado.jugador.sala, estado.jugador.velocidad,
            estado.acciones, estado.enemigos_derrotados, enemigos,
            [(o.id, eq) for o, eq in inventario.vista_detallada()],
            None if inventario.obtener_actual() is None else inventario.obtener_actual().id,
            [estado.suelo(s) for s in range(1, 7)], [estado.rastro.tiempo_en(s) for s in range(1, 7)],
            agenda, estado.azar.getstate())


class PruebasGuardadoPartida(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.partidas = os.path.join(self.carpeta.name, "partidas")

    def tearDown(self):
        self.carpeta.cleanup()

    def nueva(self, semilla=5):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta("cripta-01")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "cache")))
        version = fuente.version_catalogo()
        cache.validar_version(version)
        return ControladorPartida(datos, fuente, cache, VistaMuda(), semilla, version, self.partidas)

    def jugar(self, controlador, comandos, bitacora=None):
        pendientes = iter(comandos)
        controlador.jugar(lambda: next(pendientes, None), bitacora)
        return controlador.estado

    def test_cargar_devuelve_exactamente_lo_guardado(self):
        controlador = self.nueva()
        self.jugar(controlador, ["recoger", "sig", "esperar", "guardar prueba"])
        guardado = foto(controlador.estado)
        # en la sala 1 no hay enemigos: se puede jugar un poco sin morir antes de cargar
        self.jugar(controlador, ["esperar", "soltar", "esperar", "cargar prueba"])
        self.assertEqual(foto(controlador.estado), guardado)
        self.assertFalse(controlador.estado.terminada())

    def test_seguir_despues_de_cargar_da_lo_mismo_que_sin_guardar(self):
        antes = ["recoger", "esperar"]
        despues = ["n", "recoger itm_daga_oxidada", "sig", "equipar", "atacar e-201"]
        directo = self.nueva()
        self.jugar(directo, antes + despues)

        con_guardado = self.nueva()
        self.jugar(con_guardado, antes + ["guardar medio", "esperar", "soltar", "cargar medio"]
                   + despues)
        self.assertEqual(con_guardado.estado.acciones, directo.estado.acciones)
        self.assertEqual(foto(con_guardado.estado), foto(directo.estado))

    def test_la_antorcha_se_apaga_aunque_se_haya_cargado_la_partida(self):
        # la antorcha de cripta-01 dura 2000: con 21 esperas ya se apagó
        esperas = ["esperar"] * 21
        directo = self.nueva()
        self.jugar(directo, ["recoger", "usar"] + esperas)
        con_guardado = self.nueva()
        self.jugar(con_guardado, ["recoger", "usar", "guardar t", "cargar t"] + esperas)
        self.assertIsNone(directo.estado.antorcha_hasta)
        self.assertIsNone(con_guardado.estado.antorcha_hasta)
        self.assertEqual(foto(con_guardado.estado), foto(directo.estado))

    def test_una_puerta_abierta_despues_de_guardar_vuelve_a_cerrarse(self):
        controlador = self.nueva()
        estado = self.jugar(controlador, ["guardar inicio"])
        puerta = controlador.esqueleto.puerta(2, "E")
        puerta.abrir()
        self.jugar(controlador, ["cargar inicio"])
        self.assertTrue(controlador.esqueleto.puerta(2, "E").esta_cerrada())
        self.assertIsNot(controlador.estado, estado)

    def test_se_puede_leer_una_sala_sin_leer_todo(self):
        controlador = self.nueva()
        self.jugar(controlador, ["guardar unica"])
        with ArchivoGuardado(os.path.join(self.partidas, "unica.sav")) as archivo:
            sala = archivo.leer_sala(1)
            self.assertEqual(sala.objetos, ["itm_antorcha"])
            self.assertIsNone(archivo.leer_sala(99))

    def test_guardado_de_otra_version_no_se_carga(self):
        controlador = self.nueva()
        self.jugar(controlador, ["guardar viejo"])
        ruta = os.path.join(self.partidas, "viejo.sav")
        with self.assertRaises(GuardadoIncompatible):
            GuardadoPartida.cargar(ruta, controlador.datos, "otro-catalogo",
                                   controlador.esqueleto, controlador.cache.obtener)
        self.jugar(controlador, ["cargar no-existe"])
        self.assertTrue(any("no existe" in m for m in controlador.vista.mensajes))

    def test_la_bitacora_de_la_partida_cargada_reproduce_lo_mismo(self):
        controlador = self.nueva()
        bitacora = BitacoraPartida(os.path.join(self.partidas, "original.log"))
        bitacora.crear(CabeceraPartida("cripta-01", controlador.datos.version,
                                       controlador.version_catalogo, 5))
        self.jugar(controlador, ["recoger", "guardar g", "esperar", "soltar",
                                 "cargar g", "esperar", "n"], bitacora)
        final = foto(controlador.estado)
        cargada = controlador._bitacora_partida.ruta
        self.assertNotEqual(cargada, bitacora.ruta)
        cabecera, comandos = BitacoraPartida.leer(cargada)
        self.assertEqual(comandos, ["recoger", "esperar", "n"])
        repetida = self.nueva(semilla=cabecera.semilla)
        self.jugar(repetida, comandos)
        self.assertEqual(foto(repetida.estado), final)


if __name__ == "__main__":
    unittest.main()