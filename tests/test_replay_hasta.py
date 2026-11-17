import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

import main
from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.cliente_offline import ClienteOffline
from controlador.partida import ControladorPartida
from modelo.cache_catalogo import CacheCatalogo
from tests.fuente_memoria import VistaMuda
from vista.texto_historia import lineas_historia

COMANDOS = ["esperar", "n", "esperar", "s", "esperar"]


class PruebasReplayHasta(unittest.TestCase):
    """--replay partida.log --hasta t (spec 004, historia 2)."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self._partidas = main.CARPETA_PARTIDAS
        main.CARPETA_PARTIDAS = os.path.join(self.carpeta.name, "partidas")
        salida = io.StringIO()
        with patch("builtins.input", side_effect=COMANDOS + ["q"]), contextlib.redirect_stdout(salida):
            main.principal(["cripta-02", "--offline", "--semilla", "3"])
        nombres = os.listdir(main.CARPETA_PARTIDAS)
        self.ruta = os.path.join(main.CARPETA_PARTIDAS, nombres[0])

    def tearDown(self):
        main.CARPETA_PARTIDAS = self._partidas
        self.carpeta.cleanup()

    def esperado(self, t):
        """Lo que mostraría historia t en la misma partida jugada con el controlador."""
        fuente = ClienteOffline()
        datos = fuente.datos_cripta("cripta-02")
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(self.carpeta.name, "c")))
        cache.validar_version(fuente.version_catalogo())
        c = ControladorPartida(datos, fuente, cache, VistaMuda(), 3, fuente.version_catalogo(),
                               main.CARPETA_PARTIDAS)
        for comando in COMANDOS:
            c.ejecutar(comando)
        estado, que, instante = c.consultar_historia(str(t))
        return lineas_historia(estado, que, instante), c.estado.tiempo

    def replay(self, t):
        salida = io.StringIO()
        with patch("main.Consola", side_effect=AssertionError("no debe crear la vista")), \
                contextlib.redirect_stdout(salida):
            codigo = main.principal(["--replay", self.ruta, "--offline", "--hasta", str(t)])
        self.assertEqual(codigo, 0)
        return salida.getvalue()

    def test_mismo_resumen_que_historia(self):
        # FR-307: el resumen coincide línea por línea con historia t
        for t in (0, 120, 250):
            esperadas, _ = self.esperado(t)
            texto = self.replay(t)
            for linea in esperadas:
                self.assertIn(linea, texto)
            self.assertNotIn("> esperar", texto)      # no muestra el replay paso a paso

    def test_t_posterior_al_final(self):
        # FR-307 (Apéndice B): muestra el estado final e indica que terminó antes
        _, final = self.esperado(0)
        texto = self.replay(final + 5000)
        self.assertIn(f"termina en t={final}", texto)
        self.assertIn("Historia", texto)


if __name__ == "__main__":
    unittest.main()
