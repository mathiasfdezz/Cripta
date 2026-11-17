import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

import main


class PruebasVerificarDesdeMain(unittest.TestCase):
    """Integración de la verificación con el arranque (spec 003, historia 2)."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self._partidas = main.CARPETA_PARTIDAS
        main.CARPETA_PARTIDAS = os.path.join(self.carpeta.name, "partidas")

    def tearDown(self):
        main.CARPETA_PARTIDAS = self._partidas
        self.carpeta.cleanup()

    def correr(self, argumentos, entradas=("q",)):
        salida = io.StringIO()
        with patch("builtins.input", side_effect=list(entradas)), \
                contextlib.redirect_stdout(salida):
            codigo = main.principal(argumentos)
        return codigo, salida.getvalue()

    def test_no_resoluble_sin_forzar_no_inicia(self):
        # FR-207 (Apéndice B): cripta-05 no se puede ganar; se muestra el reporte y no empieza
        codigo, texto = self.correr(["cripta-05", "--offline", "--semilla", "1"])
        self.assertEqual(codigo, 1)
        self.assertIn("NO RESOLUBLE", texto)
        self.assertIn("Ciclo de llaves", texto)
        self.assertIn("--forzar", texto)
        self.assertNotIn("¿Qué haces?", texto)

    def test_no_resoluble_con_forzar_inicia(self):
        # FR-207, FR-209: con --forzar se muestra el reporte y la partida empieza igual
        codigo, texto = self.correr(["cripta-05", "--offline", "--forzar", "--semilla", "1"])
        self.assertEqual(codigo, 0)
        self.assertLess(texto.index("NO RESOLUBLE"), texto.index("¿Qué haces?"))

    def test_resoluble_muestra_el_reporte_antes_del_primer_turno(self):
        # FR-209
        codigo, texto = self.correr(["cripta-02", "--offline", "--semilla", "1"])
        self.assertEqual(codigo, 0)
        self.assertLess(texto.index("RESOLUBLE. Orden para conseguir las llaves"),
                        texto.index("¿Qué haces?"))

    def test_verificar_no_usa_la_vista_y_devuelve_el_codigo(self):
        # FR-208: --verificar imprime el reporte, no crea la consola y no empieza la partida
        with patch("main.Consola", side_effect=AssertionError("no debe crear la vista")):
            codigo, texto = self.correr(["--verificar", "cripta-05", "--offline"], entradas=())
            self.assertEqual(codigo, 1)
            self.assertIn("llave hierro -> llave negra -> llave hierro", texto)
            codigo, texto = self.correr(["--verificar", "cripta-06", "--offline"], entradas=())
            self.assertEqual(codigo, 0)
            self.assertIn("RESOLUBLE", texto)
        self.assertFalse(os.path.isdir(main.CARPETA_PARTIDAS))


if __name__ == "__main__":
    unittest.main()
