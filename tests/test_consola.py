import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.resumen_cripta import ResumenCripta
from tests.test_acciones import partida
from vista.consola import Consola

CRIPTAS = (ResumenCripta("cripta-01", "Osario menor", 6, 1),
           ResumenCripta("cripta-02", "Bóvedas negras", 60, 2))


def _capturar(funcion, *args):
    salida = io.StringIO()
    with redirect_stdout(salida):
        funcion(*args)
    return salida.getvalue()


class PruebasConsola(unittest.TestCase):

    def test_inventario_marca_equipado(self):
        daga = FichaCatalogo(id="itm_d", nombre="Daga", clase="arma", peso=2, valor=15)
        texto = _capturar(Consola().mostrar_inventario_detallado, [(daga, True)])
        self.assertIn("Daga [equipado]", texto)

    def test_bitacora(self):
        texto = _capturar(Consola().mostrar_bitacora, ["uno", "dos"])
        self.assertIn("uno", texto)
        self.assertIn("dos", texto)

    def test_elegir_cripta_por_numero(self):
        with patch("builtins.input", return_value="2"), redirect_stdout(io.StringIO()):
            self.assertEqual(Consola().elegir_cripta(CRIPTAS), "cripta-02")

    def test_elegir_cripta_por_id_despues_de_un_error(self):
        with patch("builtins.input", side_effect=["9", "cripta-01"]), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(Consola().elegir_cripta(CRIPTAS), "cripta-01")

    def test_sin_criptas_o_sin_entrada_no_elige(self):
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(Consola().elegir_cripta(()))
            with patch("builtins.input", side_effect=EOFError):
                self.assertIsNone(Consola().elegir_cripta(CRIPTAS))


class PruebasPantallaDeLaSala(unittest.TestCase):

    def setUp(self):
        self.estado = partida(objetos=["itm_daga", "itm_pocion"],
                              enemigos=[InstanciaEnemigo("e-1", "ent_rata"),
                                        InstanciaEnemigo("e-2", "ent_rata")])
        self.consola = Consola()

    def dibujar(self, mensajes=()):
        return _capturar(self.consola.mostrar_partida, self.estado, self.estado.esqueleto,
                         list(mensajes))

    def test_muestra_salidas_enemigos_numerados_y_suelo_legible(self):
        texto = self.dibujar()
        self.assertIn("Norte  -> ", texto)
        self.assertIn("1. Rata", texto)
        self.assertIn("2. Rata", texto)
        self.assertIn("1. daga", texto)
        self.assertIn("(itm_daga)", texto)
        self.assertIn("[####################] 30/30", texto)

    def test_atacar_y_recoger_por_numero_usan_la_ultima_pantalla(self):
        self.dibujar()
        self.assertEqual(self.consola._traducir("atacar 2"), "atacar e-2")
        self.assertEqual(self.consola._traducir("recoger 2"), "recoger itm_pocion")
        # un número que no está en pantalla se deja tal cual y el juego lo rechaza
        self.assertEqual(self.consola._traducir("atacar 9"), "atacar 9")

    def test_alias_de_comandos(self):
        traducir = self.consola._traducir
        self.assertEqual([traducir(t) for t in ("norte", "Oeste", "i", "?", "q", "z")],
                         ["n", "o", "inv", "ayuda", "salir", "esperar"])
        self.assertEqual(traducir("abrir este"), "abrir e")
        self.assertEqual(traducir("mover sur"), "s")
        self.assertEqual(traducir("recoger itm_daga"), "recoger itm_daga")

    def test_si_nada_cambio_no_repite_la_sala(self):
        self.dibujar(["Entras."])
        self.consola.mostrar_resultado("inv", ["No se puede: algo."])
        texto = self.dibujar(["Entras.", "No se puede: algo."])
        self.assertNotIn("Salidas", texto)
        self.assertEqual(texto.count("No se puede: algo."), 1)

    def test_los_mensajes_nuevos_salen_una_sola_vez_y_marcados(self):
        self.dibujar(["viejo"])
        self.estado.esperar()
        self.estado.avanzar_hasta_turno_jugador()
        self.consola.mostrar_resultado("esperar", ["nuevo"])
        texto = self.dibujar(["viejo", "nuevo"])
        self.assertIn("» nuevo", texto)
        self.assertNotIn("» viejo", texto)
        self.assertEqual(texto.count("nuevo"), 1)

    def test_sin_terminal_no_hay_codigos_de_color(self):
        self.assertNotIn("\033[", self.dibujar(["hola"]))