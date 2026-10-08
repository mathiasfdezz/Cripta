import unittest

from bench.cripta_sintetica import crear_partida
from dtos.ficha_catalogo import FichaCatalogo
from modelo.historial import Historial


class Caja:
    def __init__(self):
        self.valor = 0


class PruebasHistorial(unittest.TestCase):

    def test_deshace_valores_y_funciones_en_orden_inverso(self):
        historial = Historial()
        caja, lista = Caja(), []
        historial.abrir_intervalo()
        historial.registrar_valor(caja, "valor", caja.valor)
        caja.valor = 5
        lista.append("x")
        historial.registrar(lambda: lista.pop())
        historial.registrar_valor(caja, "valor", caja.valor)
        caja.valor = 9
        self.assertTrue(historial.deshacer())
        self.assertEqual((caja.valor, lista), (0, []))

    def test_sin_intervalo_no_se_anota_nada(self):
        historial = Historial()
        self.assertIsNone(historial.intervalo_actual())
        historial.registrar_valor(Caja(), "valor", 1)
        self.assertFalse(historial.deshacer())

    def test_el_numero_de_intervalo_nunca_se_repite(self):
        historial = Historial()
        historial.abrir_intervalo()
        primero = historial.intervalo_actual()
        historial.abrir_intervalo()
        historial.deshacer()
        historial.abrir_intervalo()
        self.assertGreater(historial.intervalo_actual(), primero + 1)

    def test_guarda_a_lo_sumo_cinco_acciones(self):
        historial = Historial()
        for _ in range(7):
            historial.abrir_intervalo()
        self.assertEqual(historial.acciones_guardadas(), 5)


class PruebasRelojUnaVezPorIntervalo(unittest.TestCase):

    def test_el_reloj_se_anota_una_sola_vez_por_accion(self):
        estado = crear_partida(10, 10, 100)
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()      # aquí actúan muchos enemigos
        pila = estado.historial._intervalos.cola.dato._datos
        anotaciones_del_reloj = [c for c in pila if isinstance(c, tuple)
                                 and c[0] is estado and c[1] == "tiempo"]
        self.assertEqual(len(anotaciones_del_reloj), 1)

    def test_deshacer_devuelve_el_reloj_al_inicio_de_la_accion(self):
        estado = crear_partida(10, 10, 100)
        estado.jugador.inventario.recoger(FichaCatalogo(
            id="itm_perg", nombre="Pergamino", clase="pergamino_retroceso", peso=1, valor=40))
        antes = estado.tiempo
        for _ in range(3):
            estado.esperar()
            estado.avanzar_hasta_turno_jugador()
        estado.deshacer()
        self.assertEqual(estado.tiempo, antes + 200)