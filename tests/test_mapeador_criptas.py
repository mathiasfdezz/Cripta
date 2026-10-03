import dataclasses
import unittest

from adaptadores.mapeadores.error_datos import ErrorDatos
from adaptadores.mapeadores.mapeador_criptas import (datos_cripta_desde_json,
                                                     resumen_cripta_desde_json)

# copiado de una respuesta real de cripta 01 para no gastar red en las pruebas
DATOS_CRIPTA = {
    "id": "cripta-01", "version": "fd58f7743b9e", "salas_total": 6, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 6,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9, "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}


class PruebasMapeadorCriptas(unittest.TestCase):

    def test_resumen_cripta(self):
        resumen = resumen_cripta_desde_json(
            {"id": "cripta-01", "nombre": "Osario menor", "salas": 6, "dificultad": 1})
        self.assertEqual(resumen.nombre, "Osario menor")

    def test_datos_cripta(self):
        datos = datos_cripta_desde_json(DATOS_CRIPTA)
        self.assertEqual(datos.presupuesto_solicitudes, 9)
        self.assertEqual(datos.jugador.velocidad, 100)

    def test_falta_un_campo(self):
        with self.assertRaises(ErrorDatos) as ctx:
            datos_cripta_desde_json({"id": "cripta-01"})
        self.assertIn("version", str(ctx.exception))

    def test_dto_no_se_puede_modificar(self):
        datos = datos_cripta_desde_json(DATOS_CRIPTA)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            datos.presupuesto_solicitudes = 999


if __name__ == "__main__":
    unittest.main()