import unittest

from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.rastro import Rastro
from tests.test_esqueleto import esqueleto, sala


def mapa_linea():
    """1 -E- 2 -E- 3 -E- 4, todas abiertas."""
    return esqueleto(sala(1, E=2), sala(2, O=1, E=3), sala(3, O=2, E=4), sala(4, O=3))


def partida(mapa, sala_jugador=1, semilla=1):
    jugador = Jugador(sala_jugador, EstadisticasJugador(1000, 6, 2, 100), Inventario(10))
    return EstadoPartida(semilla, jugador, mapa)


def ficha(comportamiento, velocidad=100):
    return FichaCatalogo(id="ent_x", nombre="X", clase="enemigo", vida_max=1000, ataque=1,
                         defensa=0, velocidad=velocidad, comportamiento=comportamiento)


def con_enemigo(estado, sala_enemigo, comportamiento, instancia="e-1", velocidad=100):
    enemigo = estado.colocar_enemigo(InstanciaEnemigo(instancia, "ent_x"),
                                     ficha(comportamiento, velocidad), sala_enemigo)
    enemigo.activo = True
    estado.programar_accion(enemigo)
    return enemigo


class PruebasCostos(unittest.TestCase):

    def test_atacar_cuesta_100(self):
        estado = partida(mapa_linea())
        estado.colocar_enemigo(InstanciaEnemigo("e-1", "ent_x"), ficha("guardián", 1), 1)
        estado.iniciar()
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 100)

    def test_el_segundo_ataque_es_en_el_siguiente_turno(self):
        estado = partida(mapa_linea())
        estado.colocar_enemigo(InstanciaEnemigo("e-1", "ent_x"), ficha("guardián", 1), 1)
        estado.iniciar()
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.tiempo, 0)
        estado.jugador_ataca("e-1")
        self.assertEqual(estado.tiempo, 100)
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 200)

    def test_abrir_puerta_cuesta_50(self):
        llave = FichaCatalogo(id="itm_llave", nombre="Llave", clase="llave", peso=1, valor=0)
        mapa = esqueleto(sala(1, E=(2, True)), sala(2, O=1))
        estado = partida(mapa)
        estado.jugador.inventario.recoger(llave)
        estado.iniciar()
        estado.abrir_puerta("E")
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 50)


class PruebasRastro(unittest.TestCase):

    def test_la_sala_inicial_tiene_rastro_en_0(self):
        estado = partida(mapa_linea())
        estado.iniciar()
        self.assertEqual(estado.rastro.tiempo_en(1), 0)
        self.assertIsNone(estado.rastro.tiempo_en(2))

    def test_moverse_marca_la_sala_destino(self):
        estado = partida(mapa_linea())
        estado.iniciar()
        estado.mover_jugador("E")
        self.assertEqual(estado.rastro.tiempo_en(2), 0)
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("E")
        self.assertEqual(estado.rastro.tiempo_en(3), 100)

    def test_mas_fresca_y_caducidad(self):
        rastro = Rastro(mapa_linea())
        rastro.marcar(1, 50)
        rastro.marcar(3, 120)
        self.assertEqual(rastro.sala_mas_fresca(2, 200), 3)
        # 120 + 399 todavía sirve; con 400 de antigüedad ya no
        self.assertEqual(rastro.sala_mas_fresca(2, 519), 3)
        self.assertIsNone(rastro.sala_mas_fresca(2, 520))

    def test_empate_gana_la_sala_de_menor_id(self):
        rastro = Rastro(mapa_linea())
        rastro.marcar(1, 80)
        rastro.marcar(3, 80)
        self.assertEqual(rastro.sala_mas_fresca(2, 100), 1)

    def test_no_mira_detras_de_puertas_cerradas(self):
        # cerrada solo desde la sala 2: el rastreador de la 2 no puede ir a la 1
        mapa = esqueleto(sala(1, E=2), sala(2, O=(1, True)))
        rastro = Rastro(mapa)
        rastro.marcar(1, 10)
        self.assertIsNone(rastro.sala_mas_fresca(2, 20))
        self.assertEqual(rastro.salidas_abiertas(2), [])
        self.assertEqual(rastro.salidas_abiertas(1), [2])


class PruebasComportamientos(unittest.TestCase):

    def test_guardian_no_deja_su_sala(self):
        estado = partida(mapa_linea())
        guardian = con_enemigo(estado, 3, "guardián")
        estado.iniciar()
        for _ in range(5):
            estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
            estado.avanzar_hasta_turno_jugador()
        self.assertEqual(guardian.sala, 3)

    def test_rastreador_sigue_el_rastro_fresco(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 3, "rastreador", velocidad=50)
        estado.iniciar()
        estado.mover_jugador("E")            # el jugador deja rastro en 2
        estado.avanzar_hasta_turno_jugador() # la rata actúa en 200 > 100: aún no
        estado.mover_jugador("O")
        estado.avanzar_hasta_turno_jugador() # en 200 la rata ve el rastro de 2 y va
        self.assertEqual(rastreador.sala, 2)

    def test_rastreador_sin_rastro_espera(self):
        estado = partida(mapa_linea())
        rastreador = con_enemigo(estado, 4, "rastreador")
        estado.iniciar()
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(rastreador.sala, 4)

    def test_errante_se_mueve_por_salidas_abiertas(self):
        mapa = esqueleto(sala(1, E=2), sala(2, O=1, E=(3, True)), sala(3, O=2))
        estado = partida(mapa, sala_jugador=1)
        errante = con_enemigo(estado, 2, "errante")
        estado.iniciar()
        visitadas = []
        for _ in range(6):
            estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
            estado.avanzar_hasta_turno_jugador()
            visitadas.append(errante.sala)
        self.assertNotIn(3, visitadas)      # nunca cruza la puerta cerrada

    def test_errante_sin_salidas_espera(self):
        mapa = esqueleto(sala(1, E=2), sala(2, O=1), sala(9))
        estado = partida(mapa)
        errante = con_enemigo(estado, 9, "errante")
        estado.iniciar()
        estado.mover_jugador("E")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(errante.sala, 9)

    def test_misma_semilla_mismos_movimientos(self):
        def correr(semilla):
            mapa = esqueleto(sala(1, E=2, S=3), sala(2, O=1, S=4), sala(3, N=1, E=4),
                             sala(4, N=2, O=3))
            estado = partida(mapa, semilla=semilla)
            errante = con_enemigo(estado, 4, "errante")
            estado.iniciar()
            recorrido = []
            for i in range(10):
                estado.mover_jugador("E" if estado.jugador.sala == 1 else "O")
                estado.avanzar_hasta_turno_jugador()
                recorrido.append(errante.sala)
            return recorrido

        self.assertEqual(correr(7), correr(7))


if __name__ == "__main__":
    unittest.main()
