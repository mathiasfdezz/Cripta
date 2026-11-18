import contextlib
import io
import unittest

from tests.criptas_prueba import enemigo, esqueleto, partida, salida
from vista.consola import Consola
from vista.menu_acciones import MenuAcciones


def pantalla(estado):
    salida_texto = io.StringIO()
    with contextlib.redirect_stdout(salida_texto):
        Consola().mostrar_partida(estado, estado.esqueleto, [])
    return salida_texto.getvalue()


class PruebasVistaTerreno(unittest.TestCase):

    def test_vista_muestra_costos_salidas(self):
        # FR-010: cada salida de la sala actual con su costo, también en el menú
        estado = partida(esqueleto(salida(1, "N", 2, 60), salida(1, "E", 3), salida(2, "S", 1)))
        texto = pantalla(estado)
        self.assertIn("costo 60", texto)
        self.assertIn("costo 100", texto)
        etiquetas = [o[0] for o in MenuAcciones().armar(estado, estado.esqueleto)]
        self.assertIn("Ir al Norte -> Sala 2 (costo 60)", etiquetas)

    def test_vista_distingue_cazadores(self):
        # FR-011: el cazador se marca distinto de errantes y rastreadores
        estado = partida(esqueleto(salida(1, "N", 2)))
        enemigo(estado, 1, "ent_sabueso", "e-1")
        enemigo(estado, 1, "ent_errante", "e-2")
        enemigo(estado, 1, "ent_rata", "e-3")
        lineas = pantalla(estado).splitlines()
        cazador = [linea for linea in lineas if "e-1" in linea][0]
        self.assertIn("CAZADOR", cazador)
        self.assertIn("rango 600", cazador)
        for instancia in ("e-2", "e-3"):
            linea = [linea for linea in lineas if instancia in linea][0]
            self.assertNotIn("CAZADOR", linea)
        etiquetas = [o[0] for o in MenuAcciones().armar(estado, estado.esqueleto)]
        self.assertTrue(any("e-1 [cazador]" in e for e in etiquetas))
        self.assertFalse(any("e-2 [cazador]" in e for e in etiquetas))


if __name__ == "__main__":
    unittest.main()
