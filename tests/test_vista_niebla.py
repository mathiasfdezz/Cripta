import contextlib
import io
import unittest

from tests.criptas_prueba import ficha, salida
from tests.fuente_memoria import controlador
from vista.consola import Consola


def ida_y_vuelta(a, direccion, b, costo=None):
    contraria = {"N": "S", "S": "N", "E": "O", "O": "E"}[direccion]
    return [salida(a, direccion, b, costo), salida(b, contraria, a, costo)]


def capturar(funcion, *args):
    texto = io.StringIO()
    with contextlib.redirect_stdout(texto):
        funcion(*args)
    return texto.getvalue()


class PruebasVistaNiebla(unittest.TestCase):

    def setUp(self):
        salidas = (ida_y_vuelta(1, "N", 2, 60) + ida_y_vuelta(2, "N", 3)
                   + [salida(2, "E", 4, 80, cerrada=True), salida(4, "O", 2)])
        self.c = controlador(salidas, vista=Consola())

    def test_la_pantalla_no_nombra_salas_avistadas(self):
        # FR-105: desde 1 la sala 2 está avistada: ni nombre ni número
        texto = capturar(self.c.vista.mostrar_partida, self.c.estado, self.c.esqueleto, [])
        self.assertIn("sala sin explorar", texto)
        self.assertNotIn("Sala 2", texto)

    def test_mapa_lista_exploradas_salidas_costos_y_avistadas(self):
        # FR-107: el comando mapa no consume tiempo y muestra lo que el jugador sabe
        self.c.ejecutar("n")
        antes = (self.c.estado.tiempo, self.c.estado.acciones)
        texto = capturar(self.c.ejecutar, "mapa")
        self.assertEqual((self.c.estado.tiempo, self.c.estado.acciones), antes)
        self.assertIn("2 exploradas, 2 avistadas", texto)
        self.assertIn("Sala 1", texto)
        self.assertIn("Sala 2", texto)
        self.assertIn("E -> sala sin explorar   costo 80  [cerrada]", texto)
        self.assertIn("S -> Sala 1 (1)   costo 60", texto)
        self.assertNotIn("Sala 3", texto)

    def test_motivo_del_viaje_visible(self):
        # FR-112: la interfaz informa por qué se detuvo el viaje
        self.c.ejecutar("n")
        self.c.ejecutar("ir a 1")
        self.assertIn("se detuvo porque llegaste a la sala 1", self.c.bitacora.ultimos()[-1])

    def test_la_precarga_sigue_usando_el_esqueleto_completo(self):
        # FR-105: el contenido de salas no exploradas se pide igual (infraestructura)
        self.assertTrue(self.c._pedidas.contiene(2))
        self.assertTrue(self.c._pedidas.contiene(3))
        self.assertEqual(self.c.estado.mapa.estado_de(3), 0)

    def test_menu_ofrece_el_mapa(self):
        opciones = [o[0] for o in self.c.vista._menu.armar(self.c.estado, self.c.esqueleto)]
        self.assertTrue(any(o.startswith("Ver el mapa conocido") for o in opciones))


if __name__ == "__main__":
    unittest.main()
