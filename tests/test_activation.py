import unittest

from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from adaptadores.mapeadores.mapeador_contenido import contenido_sala_desde_json
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.estado_partida import EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from tests.test_actores import leer_json
from tests.test_esqueleto import esqueleto, esqueleto_cripta_01, sala


def mapa_cruz():
    """La sala 1 en el centro: N->2, S->3, O->5 (todas abiertas)."""
    return esqueleto(sala(1, N=2, S=3, O=5), sala(2, S=1), sala(3, N=1), sala(5, E=1))


def ficha(velocidad=100):
    return FichaCatalogo(id="ent_rata_gigante", nombre="Rata", clase="enemigo", vida_max=12,
                         ataque=5, defensa=1, velocidad=velocidad, comportamiento="rastreador")


def partida(mapa=None, sala=1, vida=30):
    jugador = Jugador(sala, EstadisticasJugador(vida, 6, 2, 100), Inventario(10))
    return EstadoPartida(1, jugador, mapa if mapa is not None else mapa_cruz())


def colocar(estado, instancia, sala, velocidad=100, vida=None):
    return estado.colocar_enemigo(InstanciaEnemigo(instancia, "ent_rata_gigante", vida),
                                  ficha(velocidad), sala)


class PruebasActivacionInicial(unittest.TestCase):

    def test_cargar_una_sala_no_activa_a_sus_enemigos(self):
        estado = partida()
        a = colocar(estado, "e-101", 1)
        b = colocar(estado, "e-201", 2)
        for enemigo in (a, b):
            self.assertFalse(enemigo.activo)
            self.assertIsNone(enemigo.proximo_evento)
        self.assertTrue(estado.agenda.esta_vacia())

    def test_los_enemigos_de_la_sala_inicial_se_activan_desde_t0(self):
        estado = partida()
        inicial = colocar(estado, "e-101", 1)
        otra = colocar(estado, "e-201", 2)
        estado.iniciar()
        self.assertEqual(estado.tiempo, 0)
        self.assertTrue(inicial.activo)
        self.assertEqual(inicial.proximo_evento.tiempo_siguiente, 100)   # t=0 + costo 100
        self.assertFalse(otra.activo)
        self.assertIsNone(otra.proximo_evento)
        # en la agenda: el turno del jugador (t=0) y la primera accion del enemigo
        self.assertEqual(estado.agenda.tamano(), 2)
        self.assertTrue(estado.es_turno_del_jugador())

    def test_iniciar_solo_una_vez(self):
        estado = partida()
        estado.iniciar()
        with self.assertRaises(ValueError):
            estado.iniciar()

    def test_se_activan_por_orden_de_instancia(self):
        estado = partida()
        tres = colocar(estado, "e-103", 1)       # colocados en desorden a proposito
        uno = colocar(estado, "e-101", 1)
        dos = colocar(estado, "e-102", 1)
        activados = estado.activar_enemigos(1)
        self.assertEqual([e.instancia for e in activados], ["e-101", "e-102", "e-103"])
        self.assertLess(uno.proximo_evento.secuencia, dos.proximo_evento.secuencia)
        self.assertLess(dos.proximo_evento.secuencia, tres.proximo_evento.secuencia)

    def test_la_primera_accion_usa_un_costo_de_100(self):
        estado = partida()
        lento = colocar(estado, "e-101", 1, velocidad=100)
        medio = colocar(estado, "e-102", 1, velocidad=150)
        rapido = colocar(estado, "e-103", 1, velocidad=200)
        estado.activar_enemigos(1)
        # costo 100 a velocidad 100 = 100 unidades; a mas velocidad, menos tiempo
        self.assertEqual(lento.proximo_evento.tiempo_siguiente, 100)
        self.assertEqual(medio.proximo_evento.tiempo_siguiente, 66)
        self.assertEqual(rapido.proximo_evento.tiempo_siguiente, 50)

    def test_un_enemigo_muerto_no_se_activa(self):
        estado = partida()
        muerto = colocar(estado, "e-101", 1, vida=0)
        estado.iniciar()
        self.assertFalse(muerto.activo)
        self.assertIsNone(muerto.proximo_evento)
        self.assertEqual(estado.agenda.tamano(), 1)       # solo el turno del jugador


class PruebasActivacionAlEntrar(unittest.TestCase):

    def test_entrar_a_la_sala_activa_a_sus_enemigos(self):
        estado = partida()
        a = colocar(estado, "e-201", 2)
        b = colocar(estado, "e-202", 2)
        lejano = colocar(estado, "e-301", 3)
        estado.iniciar()
        self.assertFalse(a.activo or b.activo or lejano.activo)
        estado.avanzar_hasta_turno_jugador()
        self.assertFalse(a.activo)                       # aun no ha entrado

        estado.mover_jugador("N")
        self.assertTrue(a.activo and b.activo)
        self.assertFalse(lejano.activo)
        self.assertEqual(a.proximo_evento.tiempo_siguiente, 100)
        self.assertLess(a.proximo_evento.secuencia, b.proximo_evento.secuencia)

    def test_se_activan_desde_el_momento_en_que_el_jugador_entra(self):
        estado = partida()
        enemigo = colocar(estado, "e-201", 2)
        estado.iniciar()
        for direccion in ("O", "E"):                     # 1 -> 5 -> 1, sin pasar por la sala 2
            estado.mover_jugador(direccion)
            estado.avanzar_hasta_turno_jugador()
        self.assertFalse(enemigo.activo)
        self.assertEqual(estado.tiempo, 200)
        estado.mover_jugador("N")
        self.assertTrue(enemigo.activo)
        self.assertEqual(enemigo.proximo_evento.tiempo_siguiente, 300)    # 200 + 100

    def test_el_jugador_actua_primero_que_el_grupo_recien_activado(self):
        estado = partida()
        a = colocar(estado, "e-201", 2)
        estado.iniciar()
        estado.mover_jugador("N")
        # su siguiente turno y la primera accion de los enemigos caen en t=100
        self.assertEqual(a.proximo_evento.tiempo_siguiente, 100)
        self.assertEqual(estado.jugador.proximo_evento.tiempo_siguiente, 100)
        self.assertTrue(estado.es_turno_del_jugador())
        self.assertEqual(estado.avanzar_hasta_turno_jugador(), [])

    def test_los_enemigos_atacan_despues_de_activarse(self):
        estado = partida()
        colocar(estado, "e-202", 2, velocidad=150)
        colocar(estado, "e-201", 2, velocidad=150)
        estado.iniciar()
        estado.mover_jugador("N")                         # primera accion de ambos: t=66
        resultados = estado.avanzar_hasta_turno_jugador()
        self.assertEqual([r.atacante.instancia for r in resultados], ["e-201", "e-202"])
        self.assertTrue(all(r.defensor is estado.jugador for r in resultados))
        self.assertLess(estado.jugador.vida, 30)

    def test_no_se_vuelven_a_activar_al_volver_a_entrar(self):
        estado = partida()
        a = colocar(estado, "e-201", 2)
        b = colocar(estado, "e-202", 2)
        estado.iniciar()
        estado.mover_jugador("N")
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("S")
        estado.avanzar_hasta_turno_jugador()
        self.assertEqual(estado.agenda.tamano(), 3)       # jugador + 2 enemigos
        estado.mover_jugador("N")                         # vuelve a la sala 2
        self.assertEqual(estado.agenda.tamano(), 3)       # nadie se programo dos veces
        self.assertEqual(estado.activar_enemigos(2), [])
        self.assertTrue(a.activo and b.activo)

    def test_enemigo_activo_que_pasa_a_una_sala_no_visitada_sigue_activo(self):
        estado = partida()
        errante = colocar(estado, "e-201", 2)
        vecino = colocar(estado, "e-301", 3)
        estado.iniciar()
        estado.mover_jugador("N")                         # visita la 2: e-201 se activa
        estado.avanzar_hasta_turno_jugador()
        estado.mover_jugador("S")                         # y vuelve a la 1
        self.assertTrue(errante.activo)

        errante.sala = 3                                  # (el movimiento de enemigos aun no existe)
        estado.avanzar_hasta_turno_jugador()              # su evento se ejecuta: sigue en la agenda
        self.assertTrue(errante.activo)
        self.assertIsNotNone(errante.proximo_evento)
        self.assertFalse(vecino.activo)                   # la 3 sigue sin visitar
        evento_del_errante = errante.proximo_evento

        estado.mover_jugador("S")                         # el jugador entra por fin a la 3
        self.assertTrue(vecino.activo)                    # el que estaba inactivo se activa
        self.assertTrue(errante.activo)                   # el que llego activo no se toca
        self.assertIs(errante.proximo_evento, evento_del_errante)
        self.assertEqual(estado.agenda.tamano(), 3)       # jugador + 2 enemigos, sin duplicados

    def test_entrar_a_una_sala_sin_enemigos(self):
        estado = partida()
        estado.iniciar()
        self.assertEqual(estado.mover_jugador("N"), 2)
        self.assertEqual(estado.agenda.tamano(), 1)       # solo el turno del jugador


class PruebasActivacionConDatosReales(unittest.TestCase):

    def test_cripta_01(self):
        mapa = esqueleto_cripta_01()
        estado = partida(mapa, sala=1)
        ratas = ficha_catalogo_desde_json(leer_json("catalogo", "fichas", "ent_rata_gigante.json"))
        guardian = ficha_catalogo_desde_json(leer_json("catalogo", "fichas", "ent_guardian_oseo.json"))
        fichas = {"ent_rata_gigante": ratas, "ent_guardian_oseo": guardian}
        for id_sala in (2, 4):
            contenido = contenido_sala_desde_json(
                leer_json("cripta-01", "contenido", f"sala_{id_sala}.json"))
            for instancia in contenido.enemigos:
                estado.colocar_enemigo(instancia, fichas[instancia.tipo], contenido.sala)

        estado.iniciar()                                  # la sala 1 no tiene enemigos
        e201, e202, e401 = estado.enemigo("e-201"), estado.enemigo("e-202"), estado.enemigo("e-401")
        self.assertFalse(e201.activo or e202.activo or e401.activo)

        estado.mover_jugador("N")                         # entra a la sala 2
        self.assertTrue(e201.activo and e202.activo)
        self.assertFalse(e401.activo)                     # el guardian espera en la sala 4
        self.assertEqual(e201.proximo_evento.tiempo_siguiente, 66)    # rata: velocidad 150
        self.assertLess(e201.proximo_evento.secuencia, e202.proximo_evento.secuencia)


if __name__ == "__main__":
    unittest.main()