import unittest

from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.mapeadores.mapeador_llaves import llaves_desde_json


class PruebasMapeadorLlaves(unittest.TestCase):

    def test_llaves_con_y_sin_enemigo(self):
        # FR-210, FR-202: la llave que suelta un enemigo viene con la sala donde inicia
        llaves = llaves_desde_json({"llaves": [
            {"id": "itm_llave_bronce", "sala": 4},
            {"id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203"}]})
        self.assertEqual(llaves[0].enemigo, None)
        self.assertEqual((llaves[1].id, llaves[1].sala, llaves[1].enemigo),
                         ("itm_llave_negra", 12, "e-1203"))

    def test_datos_mal_formados(self):
        for malo in ({}, {"llaves": None}, {"llaves": [{"id": "x"}]},
                     {"llaves": [{"id": "x", "sala": "4"}]}):
            with self.subTest(datos=malo), self.assertRaises(ErrorDatos):
                llaves_desde_json(malo)


if __name__ == "__main__":
    unittest.main()
