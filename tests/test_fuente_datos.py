import unittest

from adaptadores.fuente_datos import validar_lote


class PruebasValidarLote(unittest.TestCase):

    def test_lote_valido(self):
        validar_lote([1, 2, 3], "contenido")

    def test_vacio_o_mas_de_10(self):
        with self.assertRaises(ValueError):
            validar_lote([], "contenido")
        with self.assertRaises(ValueError):
            validar_lote(list(range(11)), "contenido")

    def test_repetidos(self):
        with self.assertRaises(ValueError) as ctx:
            validar_lote(["itm_a", "itm_b", "itm_a"], "catálogo")
        self.assertIn("itm_a", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
