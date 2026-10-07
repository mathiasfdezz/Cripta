import unittest

from dtos.contenido_sala import ContenidoSala
from dtos.estadisticas_jugador import EstadisticasJugador
from dtos.ficha_catalogo import FichaCatalogo
from dtos.instancia_trampa import InstanciaTrampa
from modelo.estado_partida import DERROTA, SUCESO_PUERTA_CERRADA, SUCESO_TRAMPA, EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from tests.test_esqueleto import esqueleto

FICHAS = (
    FichaCatalogo(id="trp_dardos", nombre="Dardos", clase="trampa", dano=4, rearme=300),
    FichaCatalogo(id="trp_pinchos", nombre="Pinchos", clase="trampa", dano=6),
    FichaCatalogo(id="itm_llave", nombre="Llave", clase="llave", peso=1, valor=0),
    FichaCatalogo(id="itm_perg", nombre="Pergamino", clase="pergamino_retroceso", peso=1, valor=40),
)


def ficha(id_ficha):
    for f in FICHAS:
        if f.id == id_ficha:
            return f
    raise KeyError(id_ficha)


def sala(id_sala, **salidas):
    """Como la de test_esqueleto, pero con cierre automático: E=(2, True, 150)."""
    d = {}
    for direccion, valor in salidas.items():
        if isinstance(valor, tuple):
            d[direccion] = {"sala": valor[0], "cerrada": valor[1], "llave": "itm_llave",
                            "cierre_automatico": valor[2] if len(valor) > 2 else None}
        else:
            d[direccion] = {"sala": valor}
    return {"id": id_sala, "nombre": "S" + str(id_sala), "salidas": d}


def partida(trampas_sala_2=(), vida=30, pergaminos=0):
    mapa = esqueleto(sala(1, N=2, E=(3, True, 150)), sala(2, S=1), sala(3, O=1))
    jugador = Jugador(1, EstadisticasJugador(vida, 6, 2, 100), Inventario(10))
    estado = EstadoPartida(1, jugador, mapa, obtener_ficha=ficha)
    estado.cargar_contenido(ContenidoSala(1, (), (), ()))
    estado.cargar_contenido(ContenidoSala(2, (), (), tuple(trampas_sala_2)))
    estado.cargar_contenido(ContenidoSala(3, (), (), ()))
    jugador.inventario.recoger(ficha("itm_llave"))
    for _ in range(pergaminos):
        jugador.inventario.recoger(ficha("itm_perg"))
    estado.iniciar()
    return estado


def turno(estado):
    estado.avanzar_hasta_turno_jugador()


def ir_y_volver(estado):
    estado.mover_jugador("N")
    turno(estado)
    estado.mover_jugador("S")
    turno(estado)


class PruebasTrampas(unittest.TestCase):

    def test_salta_al_entrar_y_queda_desarmada(self):
        estado = partida([InstanciaTrampa("t-1", "trp_dardos")])
        estado.mover_jugador("N")
        self.assertEqual(estado.jugador.vida, 26)
        self.assertEqual(estado.tomar_sucesos(), [(SUCESO_TRAMPA, "Dardos", 4)])
        self.assertFalse(estado.trampas_en(2)[0].armada)

    def test_desarmada_no_hace_nada_y_se_rearma_despues_de_300(self):
        estado = partida([InstanciaTrampa("t-1", "trp_dardos")])
        estado.mover_jugador("N")          # t=0, salta y se rearma en 300
        turno(estado)
        estado.mover_jugador("S")          # t=100
        turno(estado)
        estado.mover_jugador("N")          # t=200: sigue desarmada
        self.assertEqual(estado.jugador.vida, 26)
        turno(estado)
        estado.mover_jugador("S")          # t=300
        turno(estado)
        self.assertTrue(estado.trampas_en(2)[0].armada)
        estado.mover_jugador("N")          # t=400: vuelve a saltar
        self.assertEqual(estado.jugador.vida, 22)

    def test_sin_rearme_en_la_ficha_usa_300(self):
        estado = partida([InstanciaTrampa("t-2", "trp_pinchos")])
        estado.mover_jugador("N")
        siguientes = sorted(t for t, _, e in estado.agenda.pendientes() if e.tipo == "rearme_trampa")
        self.assertEqual(siguientes, [300])

    def test_una_trampa_puede_matar(self):
        estado = partida([InstanciaTrampa("t-2", "trp_pinchos")], vida=5)
        estado.mover_jugador("N")
        self.assertEqual(estado.resultado, DERROTA)
        self.assertEqual(estado.jugador.vida, 0)

    def test_el_pergamino_deshace_la_trampa(self):
        estado = partida([InstanciaTrampa("t-1", "trp_dardos")], pergaminos=1)
        estado.mover_jugador("N")
        turno(estado)
        estado.deshacer()
        self.assertEqual(estado.jugador.vida, 30)
        self.assertTrue(estado.trampas_en(2)[0].armada)
        self.assertEqual(estado.jugador.sala, 1)


class PruebasCierreAutomatico(unittest.TestCase):

    def test_se_cierra_sola_despues_del_intervalo(self):
        estado = partida()
        estado.abrir_puerta("E")            # t=0: el cierre queda programado para t=150
        self.assertTrue(estado.esqueleto.puede_atravesar(1, "E"))
        turno(estado)
        estado.esperar()                    # t=50: sigue abierta
        self.assertTrue(estado.esqueleto.puede_atravesar(1, "E"))
        turno(estado)                       # llega a t=150: el cierre se programó antes, va primero
        self.assertFalse(estado.esqueleto.puede_atravesar(1, "E"))
        self.assertIn((SUCESO_PUERTA_CERRADA, 1, "E"), estado.tomar_sucesos())

    def test_quien_ya_cruzo_se_queda_del_otro_lado(self):
        estado = partida()
        estado.abrir_puerta("E")
        turno(estado)
        estado.mover_jugador("E")           # t=50, cruza a la sala 3
        turno(estado)
        estado.esperar()                    # t=150: la puerta 1-E se cierra
        turno(estado)
        self.assertEqual(estado.jugador.sala, 3)
        self.assertFalse(estado.esqueleto.puede_atravesar(1, "E"))
        # el lado de la sala 3 es otra puerta y sigue abierto
        self.assertTrue(estado.esqueleto.puede_atravesar(3, "O"))

    def test_una_puerta_sin_cierre_automatico_queda_abierta(self):
        estado = partida()
        estado.esqueleto.puerta(1, "E").cierre_automatico = None
        estado.abrir_puerta("E")
        for _ in range(5):
            turno(estado)
            estado.esperar()
        self.assertTrue(estado.esqueleto.puede_atravesar(1, "E"))


if __name__ == "__main__":
    unittest.main()