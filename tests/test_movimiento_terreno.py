import unittest

from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from tests.criptas_prueba import enemigo, esqueleto, ficha, partida, ronda, salida


def proximo_turno(estado):
    return estado.jugador.proximo_evento.tiempo_siguiente


class PruebasCostoDeLasSalidas(unittest.TestCase):
    """Terreno: moverse cuesta el costo de la salida (spec 001, historia 1)."""

    def test_intervalo_movimiento_costo_variable(self):
        # FR-002, FR-003: velocidad 200 por una salida de costo 50 -> max(1, 50*100//200) = 25
        estado = partida(esqueleto(salida(1, "N", 2, costo=50)), velocidad=200)
        estado.mover_jugador("N")
        self.assertEqual(proximo_turno(estado), 25)

    def test_intervalo_velocidad_alta_costo_uno(self):
        # FR-003 (Apéndice B): velocidad 1000 por una salida de costo 1 -> el intervalo es 1
        estado = partida(esqueleto(salida(1, "N", 2, costo=1)), velocidad=1000)
        estado.mover_jugador("N")
        self.assertEqual(proximo_turno(estado), 1)

    def test_sin_costo_declarado_cuesta_100(self):
        # FR-001
        estado = partida(esqueleto(salida(1, "N", 2)))
        estado.mover_jugador("N")
        self.assertEqual(proximo_turno(estado), 100)

    def test_el_costo_es_el_de_la_salida_de_cada_sentido(self):
        # FR-001, FR-002: ida y vuelta por la misma conexión
        estado = partida(esqueleto(salida(1, "E", 2, costo=250), salida(2, "O", 1, costo=250)))
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("O")
        self.assertEqual(proximo_turno(estado), 500)

    def test_reescalado_velocidad_salida_costosa(self):
        # FR-013 (Apéndice B): la poción rápida dura 100 y sube la velocidad a 200
        estado = partida(esqueleto(salida(1, "N", 2, costo=500)))
        estado.jugador.inventario.recoger(ficha("itm_rapida"))
        estado.usar()                                  # t=0, cuesta 50 a velocidad 200 -> 25
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.tiempo, 25)
        estado.mover_jugador("N")                      # 500*100//200 = 250 -> turno en 275
        evento_antes = estado.jugador.proximo_evento
        self.assertEqual(evento_antes.tiempo_siguiente, 275)
        estado.avanzar_hasta_turno_jugador()           # en t=100 vuelve a velocidad 100
        # restante (275-100)=175 a velocidad 200 -> 175*200//100 = 350 -> turno en 450
        evento = estado.jugador.proximo_evento
        self.assertEqual(estado.jugador.velocidad, 100)
        self.assertEqual(evento.tiempo_siguiente, 450)
        self.assertGreater(evento.secuencia, evento_antes.secuencia)
        self.assertTrue(evento_antes.cancelado)

    def test_costos_acciones_no_cambian(self):
        # FR-012: atacar y esperar 100, usar y equipar 50, recoger y soltar 25, abrir 50
        mapa = esqueleto(salida(1, "N", 2, costo=7, cerrada=True, llave="itm_llave"))
        estado = partida(mapa, contenido=[ContenidoSala(1, (), ("itm_daga", "itm_pocion"), ())])
        casos = (
            (lambda: estado.recoger("itm_daga"), 25),
            (lambda: estado.equipar(), 50),
            (lambda: estado.recoger("itm_pocion"), 25),
            (lambda: estado.soltar(), 25),
            (lambda: (estado.jugador.inventario.recoger(ficha("itm_llave")),
                      estado.abrir_puerta("N")), 50),
            (lambda: estado.esperar(), 100),
        )
        for accion, costo in casos:
            antes = estado.tiempo
            accion()
            self.assertEqual(proximo_turno(estado) - antes, costo)
            estado.avanzar_hasta_turno_jugador()
        # atacar a un guardián en la sala
        guardia = estado.colocar_enemigo(InstanciaEnemigo("g-1", "ent_guardia"),
                                         ficha("ent_guardia"), 1)
        antes = estado.tiempo
        estado.jugador_ataca(guardia.instancia)
        self.assertEqual(proximo_turno(estado) - antes, 100)


class PruebasEnemigosPorTerreno(unittest.TestCase):
    """Errantes y rastreadores conservan su comportamiento; solo cambia lo que tarda
    su movimiento (FR-003)."""

    def test_errante_tarda_el_costo_de_la_salida(self):
        estado = partida(esqueleto(salida(5, "N", 6, costo=300), salida(1, "N", 2)))
        errante = enemigo(estado, 5, "ent_errante")    # primera acción en t=100
        ronda(estado)
        self.assertEqual(errante.sala, 6)
        self.assertEqual(errante.proximo_evento.tiempo_siguiente, 100 + 300)

    def test_rastreador_tarda_el_costo_de_la_salida(self):
        mapa = esqueleto(salida(1, "E", 2, costo=40), salida(2, "O", 1, costo=40),
                         salida(2, "E", 3, costo=40), salida(3, "O", 2, costo=40))
        estado = partida(mapa, sala_jugador=2)
        estado.mover_jugador("O")                      # deja rastro en 2 (t=0) y llega a 1
        rata = enemigo(estado, 3, "ent_rata")
        estado.avanzar_hasta_turno_jugador()
        estado.esperar()
        estado.avanzar_hasta_turno_jugador()           # la rata actúa en t=100
        self.assertEqual(rata.sala, 2)
        self.assertEqual(rata.proximo_evento.tiempo_siguiente, 100 + 40)

    def test_guardian_espera_100(self):
        estado = partida(esqueleto(salida(5, "N", 6, costo=10), salida(1, "N", 2)))
        guardia = enemigo(estado, 5, "ent_guardia")
        ronda(estado)
        self.assertEqual(guardia.sala, 5)
        self.assertEqual(guardia.proximo_evento.tiempo_siguiente, 200)


if __name__ == "__main__":
    unittest.main()
