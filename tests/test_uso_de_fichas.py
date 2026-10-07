import os
import tempfile
import unittest

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.rutas_offline import RutasOffline
from controlador.partida import ControladorPartida
from controlador.uso_de_fichas import UsoDeFichas
from dtos.ficha_catalogo import FichaCatalogo
from modelo.cache_catalogo import CacheCatalogo
from tests.test_partida import CARPETA_OFFLINE, VistaMuda


class FuenteFalsa:
    def catalogo(self, ids):
        return [FichaCatalogo(id=i, nombre=i, clase="arma", peso=1, valor=1) for i in ids]


class PruebasUsoDeFichas(unittest.TestCase):

    def test_retiene_lo_nuevo_y_libera_lo_que_ya_no_se_usa(self):
        cache = CacheCatalogo(FuenteFalsa(), capacidad=5)
        uso = UsoDeFichas(cache)
        uso.actualizar(["b", "a", "b"])
        self.assertEqual(uso.retenidas(), ["a", "b"])
        self.assertEqual((cache.referencias("a"), cache.referencias("b")), (1, 1))
        uso.actualizar(["b", "c"])
        self.assertEqual((cache.referencias("a"), cache.referencias("b"), cache.referencias("c")),
                         (0, 1, 1))

    def test_una_ficha_en_uso_no_sale_aunque_la_cache_este_llena(self):
        cache = CacheCatalogo(FuenteFalsa(), capacidad=2)
        uso = UsoDeFichas(cache)
        uso.actualizar(["a"])
        cache.resolver(["b", "c", "d"])          # muchas fichas nuevas: hay que desalojar
        self.assertTrue(cache.esta_en_memoria("a"))
        uso.actualizar([])                         # ya no se usa: puede salir
        cache.resolver(["e", "f"])
        self.assertFalse(cache.esta_en_memoria("a"))

    def test_si_la_ficha_ya_salio_se_trae_antes_de_retenerla(self):
        cache = CacheCatalogo(FuenteFalsa(), capacidad=1)
        cache.resolver(["a"])
        cache.resolver(["b"])                      # "a" sale de memoria
        UsoDeFichas(cache).actualizar(["a"])
        self.assertEqual(cache.referencias("a"), 1)


class PruebasUsoEnLaPartida(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def test_con_una_cache_de_2_lo_que_se_usa_sigue_en_memoria(self):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta("cripta-01")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "c")),
                              capacidad=2)
        cache.validar_version(fuente.version_catalogo())
        controlador = ControladorPartida(datos, fuente, cache, VistaMuda(), 4)
        for comando in ["recoger", "n", "recoger itm_daga_oxidada", "esperar"]:
            controlador.ejecutar(comando)
            for id_ficha in controlador.estado.fichas_en_uso():
                self.assertTrue(cache.esta_en_memoria(id_ficha), id_ficha)
                self.assertGreater(cache.referencias(id_ficha), 0, id_ficha)

    def test_las_fichas_en_uso_de_la_sala_2(self):
        fuente = ClienteOffline(RutasOffline(CARPETA_OFFLINE))
        datos = fuente.datos_cripta("cripta-01")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "c")))
        cache.validar_version(fuente.version_catalogo())
        controlador = ControladorPartida(datos, fuente, cache, VistaMuda(), 4)
        controlador.ejecutar("n")
        en_uso = controlador.estado.fichas_en_uso()
        for id_ficha in ("ent_rata_gigante", "itm_daga_oxidada", "trp_dardos"):
            self.assertIn(id_ficha, en_uso)
        # la antorcha quedó en el suelo de la sala 1: ya no está en uso
        self.assertNotIn("itm_antorcha", en_uso)


if __name__ == "__main__":
    unittest.main()