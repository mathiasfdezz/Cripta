import unittest

from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json


class PruebasMapeadorContenido(unittest.TestCase):

    def test_enemigo_sin_vida(self):
        contenido = contenido_sala_desde_json({
            "sala": 4,
            "enemigos": [{"instancia": "e-401", "tipo": "ent_guardian_oseo"}],
            "objetos": ["itm_llave_negra", "itm_pocion_menor"],
            "trampas": [],
        })
        self.assertIsNone(contenido.enemigos[0].vida)
        self.assertEqual(contenido.objetos, ("itm_llave_negra", "itm_pocion_menor"))

    def test_enemigos_y_trampas(self):
        contenido = contenido_sala_desde_json({
            "sala": 2,
            "enemigos": [{"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 12}],
            "objetos": [],
            "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}],
        })
        self.assertEqual(contenido.enemigos[0].vida, 12)
        self.assertEqual(contenido.trampas[0].tipo, "trp_dardos")


if __name__ == "__main__":
    unittest.main()