import unittest

from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json


class PruebasMapeadorCatalogo(unittest.TestCase):

    def test_trampa_campo_dano(self):
        ficha = ficha_catalogo_desde_json(
            {"id": "trp_dardos", "nombre": "Dardos en la pared", "clase": "trampa",
             "daño": 4, "rearme": 300})
        self.assertEqual(ficha.dano, 4)
        self.assertIsNone(ficha.velocidad)

    def test_enemigo_suelta(self):
        ficha = ficha_catalogo_desde_json(
            {"id": "ent_rata_gigante", "nombre": "Rata gigante", "clase": "enemigo",
             "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
             "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]})
        self.assertEqual(ficha.suelta, ("itm_pocion_menor",))

    def test_suelta_null(self):
        ficha = ficha_catalogo_desde_json(
            {"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 5, "ataque": 1,
             "defensa": 0, "velocidad": 100, "comportamiento": "errante", "suelta": None})
        self.assertEqual(ficha.suelta, ())

    def test_falta_campo_obligatorio_de_su_clase(self):
        with self.assertRaises(ErrorDatos) as ctx:
            ficha_catalogo_desde_json(
                {"id": "itm_espada", "nombre": "Espada", "clase": "arma", "peso": 3, "valor": 10})
        self.assertIn("ataque_bonus", str(ctx.exception))


    def test_clase_desconocida_no_rompe_la_carga(self):
        ficha = ficha_catalogo_desde_json({"id": "x", "nombre": "X", "clase": "dragon"})
        self.assertEqual(ficha.clase, "dragon")

    def test_comportamiento_desconocido(self):
        with self.assertRaises(ErrorDatos):
            ficha_catalogo_desde_json(
                {"id": "ent_x", "nombre": "X", "clase": "enemigo", "vida_max": 5, "ataque": 1,
                 "defensa": 0, "velocidad": 100, "comportamiento": "volador"})


if __name__ == "__main__":
    unittest.main()
