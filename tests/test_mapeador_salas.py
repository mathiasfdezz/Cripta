import unittest

from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json, sala_desde_json

SALA_2 = {
    "id": 2, "nombre": "Pasillo de las urnas",
    "salidas": {
        "S": {"sala": 1},
        "N": {"sala": 3},
        "E": {"sala": 5, "cerrada": True, "llave": "itm_llave_bronce", "cierre_automatico": 500},
    },
}


class PruebasMapeadorSalas(unittest.TestCase):

    def test_salidas_en_orden_fijo(self):
        sala = sala_desde_json(SALA_2)
        self.assertEqual([s.direccion for s in sala.salidas], ["N", "S", "E"])

    def test_salida_cerrada_y_abierta(self):
        norte, sur, este = sala_desde_json(SALA_2).salidas
        self.assertFalse(norte.cerrada)
        self.assertIsNone(norte.llave)
        self.assertTrue(este.cerrada)
        self.assertEqual(este.llave, "itm_llave_bronce")
        self.assertEqual(este.cierre_automatico, 500)

    def test_direccion_desconocida(self):
        with self.assertRaises(ErrorDatos):
            sala_desde_json({"id": 9, "nombre": "X", "salidas": {"NE": {"sala": 1}}})

    def test_pagina_de_salas(self):
        pagina = pagina_salas_desde_json({"pagina": 1, "total_paginas": 1, "salas": [SALA_2]})
        self.assertEqual(len(pagina.salas), 1)
        self.assertEqual(pagina.salas[0].nombre, "Pasillo de las urnas")

    def test_sala_sin_salidas(self):
        sala = sala_desde_json({"id": 6, "nombre": "Salida"})
        self.assertEqual(sala.salidas, ())

    def test_cerrada_null_es_abierta(self):
        sala = sala_desde_json({"id": 1, "nombre": "A", "salidas": {
            "N": {"sala": 2, "cerrada": None, "llave": None, "cierre_automatico": None}}})
        self.assertFalse(sala.salidas[0].cerrada)

    # FR-001: costo de las salidas

    def test_costo_ausente_o_null_vale_100(self):
        sala = sala_desde_json({"id": 1, "nombre": "A", "salidas": {
            "N": {"sala": 2}, "S": {"sala": 3, "costo": None}, "E": {"sala": 4, "costo": 250}}})
        self.assertEqual([s.costo for s in sala.salidas], [100, 100, 250])

    def test_costo_invalido_es_error_de_datos(self):
        for malo in (0, -5, 2.5, "100", True):
            with self.subTest(costo=malo), self.assertRaises(ErrorDatos):
                sala_desde_json({"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "costo": malo}}})


if __name__ == "__main__":
    unittest.main()
