import os
import tempfile
import unittest

from adaptadores.cliente_offline import ClienteOffline
from adaptadores.error_fuente_datos import ErrorFuenteDatos
from adaptadores.error_offline import ErrorOffline
from adaptadores.fuente_datos import FuenteDatos
from adaptadores.rutas_offline import RutasOffline

# usa los datos reales de cripta-01 que están en el repo
CARPETA = os.path.join(os.path.dirname(__file__), "..", "datos_offline")


class PruebasClienteOffline(unittest.TestCase):

    def setUp(self):
        self.cliente = ClienteOffline(RutasOffline(CARPETA))

    def test_cumple_el_contrato(self):
        self.assertIsInstance(self.cliente, FuenteDatos)

    def test_datos_de_la_cripta(self):
        datos = self.cliente.datos_cripta("cripta-01")
        self.assertEqual(datos.sala_inicial, 1)
        self.assertEqual(self.cliente.version_cripta("cripta-01"), datos.version)

    def test_cualquier_combinacion_de_salas(self):
        contenidos = self.cliente.contenido("cripta-01", [5, 2])
        self.assertEqual([c.sala for c in contenidos], [5, 2])
        self.assertEqual(contenidos[1].enemigos[0].instancia, "e-201")

    def test_catalogo_y_esqueleto(self):
        rata, = self.cliente.catalogo(["ent_rata_gigante"])
        self.assertEqual(rata.velocidad, 150)
        pagina = self.cliente.pagina_salas("cripta-01", 1)
        self.assertEqual(len(pagina.salas), 6)

    def test_no_gasta_solicitudes(self):
        self.cliente.fijar_presupuesto(9)
        self.cliente.listar_criptas()
        self.cliente.catalogo(["itm_antorcha", "trp_dardos"])
        self.assertEqual(self.cliente.solicitudes_realizadas(), 0)

    def test_falta_un_archivo(self):
        with self.assertRaises(ErrorOffline) as ctx:
            self.cliente.datos_cripta("cripta-99")
        self.assertIn("descargar_offline", str(ctx.exception))

    def test_archivo_danado(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with open(os.path.join(carpeta, "criptas.json"), "w", encoding="utf-8") as archivo:
                archivo.write("{esto no es json")
            with self.assertRaises(ErrorFuenteDatos):
                ClienteOffline(RutasOffline(carpeta)).listar_criptas()

    def test_lote_de_11(self):
        with self.assertRaises(ValueError):
            self.cliente.catalogo([f"id_{i}" for i in range(11)])


if __name__ == "__main__":
    unittest.main()