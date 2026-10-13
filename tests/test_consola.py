import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from dtos.ficha_catalogo import FichaCatalogo
from dtos.resumen_cripta import ResumenCripta
from vista.consola import Consola

CRIPTAS = (ResumenCripta("cripta-01", "Osario menor", 6, 1),
           ResumenCripta("cripta-02", "Bóvedas negras", 60, 2))


def _capturar(funcion, *args):
    salida = io.StringIO()
    with redirect_stdout(salida):
        funcion(*args)
    return salida.getvalue()


class PruebasConsola(unittest.TestCase):

    def test_inventario_marca_equipado(self):
        daga = FichaCatalogo(id="itm_d", nombre="Daga", clase="arma", peso=2, valor=15)
        texto = _capturar(Consola().mostrar_inventario_detallado, [(daga, True)])
        self.assertIn("Daga [equipado]", texto)

    def test_bitacora(self):
        texto = _capturar(Consola().mostrar_bitacora, ["uno", "dos"])
        self.assertIn("uno", texto)
        self.assertIn("dos", texto)

    def test_elegir_cripta_por_numero(self):
        with patch("builtins.input", return_value="2"), redirect_stdout(io.StringIO()):
            self.assertEqual(Consola().elegir_cripta(CRIPTAS), "cripta-02")

    def test_elegir_cripta_por_id_despues_de_un_error(self):
        with patch("builtins.input", side_effect=["9", "cripta-01"]), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(Consola().elegir_cripta(CRIPTAS), "cripta-01")

    def test_sin_criptas_o_sin_entrada_no_elige(self):
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(Consola().elegir_cripta(()))
            with patch("builtins.input", side_effect=EOFError):
                self.assertIsNone(Consola().elegir_cripta(CRIPTAS))