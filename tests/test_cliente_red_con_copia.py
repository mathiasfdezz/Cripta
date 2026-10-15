import os
import tempfile
import unittest

from adaptadores.cliente_red_con_copia import ID_SEGURO, ClienteRedConCopia


class ConexionFalsa:
    """Responde como el API desde memoria y anota cada solicitud que llega a la "red"."""

    def __init__(self, version="v1"):
        self.client_id = "prueba"
        self.version = version
        self.rutas = []

    def fijar_presupuesto(self, presupuesto):
        pass

    def solicitudes_realizadas(self):
        return len(self.rutas)

    def obtener_json(self, ruta, operacion):
        self.rutas.append(ruta)
        if ruta == "/criptas/c1":
            return {"id": "c1", "version": self.version, "salas_total": 3, "paginas": 1,
                    "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 3,
                    "llave_salida": "itm_llave", "presupuesto_solicitudes": 9,
                    "inventario_max": 5,
                    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}}
        if ruta.startswith("/criptas/c1/salas"):
            return {"pagina": 1, "total_paginas": 1, "salas": [
                {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}}},
                {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}, "N": {"sala": 3}}},
                {"id": 3, "nombre": "C", "salidas": {"S": {"sala": 2}}}]}
        if ruta.startswith("/criptas/c1/contenido?salas="):
            salas = ruta.split("=")[1].split(",")
            return {"contenido": [{"sala": int(s), "enemigos": [], "objetos": [f"itm_{s}"],
                                   "trampas": []} for s in salas]}
        raise AssertionError(f"ruta inesperada {ruta}")


class PruebasClienteRedConCopia(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.carpeta.cleanup()

    def cliente(self, version="v1"):
        conexion = ConexionFalsa(version)
        return ClienteRedConCopia(conexion, self.carpeta.name), conexion

    def jugar(self, cliente):
        cliente.datos_cripta("c1")
        pagina = cliente.pagina_salas("c1", 1)
        contenido = cliente.contenido("c1", [1, 2, 3])
        return pagina, contenido

    def test_la_segunda_partida_no_pide_esqueleto_ni_contenido(self):
        primero, red1 = self.cliente()
        esperado = self.jugar(primero)
        segundo, red2 = self.cliente()
        self.assertEqual(self.jugar(segundo), esperado)
        self.assertEqual(len(red1.rutas), 3)
        self.assertEqual(red2.rutas, ["/criptas/c1"])

    def test_si_cambia_la_version_se_descarta_lo_guardado(self):
        self.jugar(self.cliente("v1")[0])
        nuevo, red = self.cliente("v2")
        self.jugar(nuevo)
        self.assertEqual(len(red.rutas), 3)

    def test_solo_pide_las_salas_que_faltan_y_respeta_el_orden(self):
        cliente, red = self.cliente()
        cliente.datos_cripta("c1")
        cliente.contenido("c1", [2])
        contenidos = cliente.contenido("c1", [3, 2, 1])
        self.assertEqual([c.sala for c in contenidos], [3, 2, 1])
        self.assertEqual(red.rutas[-1], "/criptas/c1/contenido?salas=3,1")

    def test_un_archivo_danado_se_vuelve_a_pedir(self):
        self.jugar(self.cliente()[0])
        ruta = os.path.join(self.carpeta.name, "c1", "contenido", "sala_2.json")
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("{no es json")
        cliente, red = self.cliente()
        cliente.datos_cripta("c1")
        contenidos = cliente.contenido("c1", [1, 2, 3])
        self.assertEqual([c.objetos for c in contenidos], [("itm_1",), ("itm_2",), ("itm_3",)])
        self.assertEqual(red.rutas[-1], "/criptas/c1/contenido?salas=2")

    def test_sin_datos_de_la_cripta_no_usa_la_copia(self):
        cliente, red = self.cliente()
        cliente.pagina_salas("c1", 1)
        self.assertEqual(os.listdir(self.carpeta.name), [])

    def test_solo_ids_simples_se_usan_como_carpeta(self):
        # así un id como "../algo" nunca puede borrar nada fuera de la caché
        self.assertIsNotNone(ID_SEGURO.match("cripta-04"))
        self.assertIsNone(ID_SEGURO.match("../c1"))
        self.assertIsNone(ID_SEGURO.match("c1/salas"))


if __name__ == "__main__":
    unittest.main()
