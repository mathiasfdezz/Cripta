import json
import os
import tempfile
import unittest

from adaptadores.descargador_offline import DescargadorOffline
from adaptadores.rutas_offline import RutasOffline

RESPUESTAS = {
    "/criptas": {"criptas": [{"id": "c1", "nombre": "Prueba", "salas": 2, "dificultad": 1}]},
    "/criptas/c1": {"id": "c1", "paginas": 1},
    "/criptas/c1/version": {"id": "c1", "version": "v1"},
    "/criptas/c1/salas?pagina=1": {"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}}},
    ]},
    "/criptas/c1/contenido?salas=1,2": {"contenido": [
        {"sala": 1, "enemigos": [], "objetos": ["itm_daga"], "trampas": []},
        {"sala": 2, "enemigos": [{"instancia": "e-1", "tipo": "ent_rata"}], "objetos": [],
         "trampas": []},
    ]},
    "/catalogo/version": {"version": "cat-1"},
    "/catalogo?ids=itm_daga,ent_rata": {"entidades": [
        {"id": "itm_daga", "nombre": "Daga", "clase": "arma"},
        {"id": "ent_rata", "nombre": "Rata", "clase": "enemigo", "suelta": ["itm_pocion"]},
    ]},
    "/catalogo?ids=itm_pocion": {"entidades": [
        {"id": "itm_pocion", "nombre": "Poción", "clase": "pocion"},
    ]},
}


class ConexionFalsa:
    def __init__(self):
        self.rutas_pedidas = []

    def obtener_json(self, ruta, operacion):
        self.rutas_pedidas.append(ruta)
        return RESPUESTAS[ruta]


class PruebasDescargadorOffline(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.rutas = RutasOffline(self.carpeta.name)
        self.conexion = ConexionFalsa()
        self.descargador = DescargadorOffline(self.conexion, self.rutas)

    def tearDown(self):
        self.carpeta.cleanup()

    def leer(self, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)

    def test_lista_de_criptas(self):
        self.assertEqual(self.descargador.descargar_lista_criptas(), ["c1"])
        self.assertTrue(os.path.exists(self.rutas.criptas()))

    def test_contenido_un_archivo_por_sala(self):
        self.descargador.descargar_cripta("c1")
        sala_2 = self.leer(self.rutas.contenido_sala("c1", 2))
        self.assertEqual(sala_2["enemigos"][0]["instancia"], "e-1")
        self.assertTrue(os.path.exists(self.rutas.pagina_salas("c1", 1)))
        self.assertTrue(os.path.exists(self.rutas.version_cripta("c1")))

    def test_descarga_tambien_lo_que_sueltan_los_enemigos(self):
        self.descargador.descargar_cripta("c1")
        self.assertEqual(self.leer(self.rutas.ficha("itm_pocion"))["nombre"], "Poción")
        self.assertIn("/catalogo?ids=itm_pocion", self.conexion.rutas_pedidas)


if __name__ == "__main__":
    unittest.main()