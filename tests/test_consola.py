import io
import unittest
from contextlib import redirect_stdout

from dtos.ficha_catalogo import FichaCatalogo
from modelo.bitacora import Bitacora
from modelo.inventario import Inventario
from controlador.controlador import Controlador
from vista.consola import Consola


def _capturar(funcion, *args):
    salida = io.StringIO()
    with redirect_stdout(salida):
        funcion(*args)
    return salida.getvalue()


class PruebasConsola(unittest.TestCase):

    def test_mensaje(self):
        self.assertIn("hola", _capturar(Consola().mostrar_mensaje, "hola"))

    def test_inventario_marca_equipado(self):
        daga = FichaCatalogo(id="itm_d", nombre="Daga", clase="arma", peso=2, valor=15)
        texto = _capturar(Consola().mostrar_inventario_detallado, [(daga, True)])
        self.assertIn("Daga [equipado]", texto)

    def test_bitacora(self):
        texto = _capturar(Consola().mostrar_bitacora, ["uno", "dos"])
        self.assertIn("uno", texto)
        self.assertIn("dos", texto)

    def test_controlador_con_consola_real(self):
        daga = FichaCatalogo(id="itm_d", nombre="Daga", clase="arma", peso=2, valor=15)
        ctl = Controlador(Inventario(3), Consola(), Bitacora())
        _capturar(ctl.recoger_objeto, daga)
        _capturar(ctl.mostrar_inventario)
        _capturar(ctl.mostrar_bitacora)
        _capturar(ctl.soltar_objeto)


if __name__ == "__main__":
    unittest.main()