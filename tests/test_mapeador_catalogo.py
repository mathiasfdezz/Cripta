import unittest

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


if __name__ == "__main__":
    unittest.main()