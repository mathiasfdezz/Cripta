import unittest
from unittest.mock import Mock, patch

import requests

from adaptadores.cliente_red import ClienteRed
from adaptadores.error_presupuesto import ErrorPresupuesto
from adaptadores.error_red import ErrorRed


DATOS_CRIPTA = {
    "id": "cripta-01", "version": "fd58f7743b9e", "salas_total": 6, "paginas": 1,
    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 6,
    "llave_salida": "itm_llave_negra", "presupuesto_solicitudes": 9, "inventario_max": 10,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}


def respuesta(codigo, cuerpo=None):
    falsa = Mock()
    falsa.status_code = codigo
    falsa.json.return_value = cuerpo if cuerpo is not None else {}
    falsa.text = str(cuerpo)
    return falsa


def cliente_sin_espera():
    return ClienteRed(esperar=lambda segundos: None)


# requests.get se reemplaza por uno falso, estas pruebas no usan la red
@patch("adaptadores.cliente_red.requests.get")
class PruebasClienteRed(unittest.TestCase):

    def test_200_devuelve_dto(self, get):
        get.return_value = respuesta(200, DATOS_CRIPTA)
        datos = cliente_sin_espera().datos_cripta("cripta-01")
        self.assertEqual(datos.presupuesto_solicitudes, 9)

    def test_mismo_client_id_en_todas(self, get):
        get.return_value = respuesta(200, {"version": "abc"})
        cliente = cliente_sin_espera()
        cliente.version_catalogo()
        cliente.version_catalogo()
        ids = [llamada.kwargs["headers"]["X-Cripta-Client-Id"] for llamada in get.call_args_list]
        self.assertEqual(ids, [cliente.client_id, cliente.client_id])

    def test_429_reintenta_y_cuenta(self, get):
        get.side_effect = [respuesta(429, {"error": "x", "reintentar_en": 3}),
                           respuesta(200, {"version": "abc"})]
        avisos = []
        cliente = ClienteRed(esperar=lambda s: None,
                             al_esperar=lambda op, seg, intento: avisos.append(seg))
        self.assertEqual(cliente.version_catalogo(), "abc")
        self.assertEqual(cliente.solicitudes_realizadas(), 2)
        self.assertEqual(avisos, [3])

    def test_429_siempre_agota_reintentos(self, get):
        get.return_value = respuesta(429, {"reintentar_en": 1})
        cliente = cliente_sin_espera()
        with self.assertRaises(ErrorRed):
            cliente.version_catalogo()
        self.assertEqual(cliente.solicitudes_realizadas(), 3)

    def test_presupuesto_agotado_no_envia(self, get):
        get.return_value = respuesta(200, {"version": "abc"})
        cliente = cliente_sin_espera()
        cliente.fijar_presupuesto(1)
        cliente.version_catalogo()
        with self.assertRaises(ErrorPresupuesto):
            cliente.version_catalogo()
        self.assertEqual(get.call_count, 1)

    def test_404_con_contexto(self, get):
        get.return_value = respuesta(404, {"error": "Not found"})
        with self.assertRaises(ErrorRed) as ctx:
            cliente_sin_espera().datos_cripta("cripta-99")
        self.assertIn("cripta-99", str(ctx.exception))
        self.assertIn("404", str(ctx.exception))

    def test_timeout_con_contexto(self, get):
        get.side_effect = requests.Timeout()
        with self.assertRaises(ErrorRed) as ctx:
            cliente_sin_espera().version_catalogo()
        self.assertIn("no respondió", str(ctx.exception))

    def test_lote_de_11_no_gasta_solicitud(self, get):
        cliente = cliente_sin_espera()
        with self.assertRaises(ValueError):
            cliente.catalogo([f"id_{i}" for i in range(11)])
        get.assert_not_called()
        self.assertEqual(cliente.solicitudes_realizadas(), 0)


if __name__ == "__main__":
    unittest.main()