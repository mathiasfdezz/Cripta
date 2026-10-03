import unittest

from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento


class PruebasAgendaEventos(unittest.TestCase):

    def test_secuencia_creciente(self):
        agenda = AgendaEventos()
        s1 = agenda.programar(100, Evento("accion", "jugador"))
        s2 = agenda.programar(50, Evento("accion", "e-201"))
        s3 = agenda.programar(100, Evento("veneno", "jugador"))
        self.assertEqual((s1, s2, s3), (1, 2, 3))

    def test_empate_lo_decide_la_secuencia(self):
        agenda = AgendaEventos()
        rata = Evento("accion", "e-201")
        jugador = Evento("accion", "jugador")
        veneno = Evento("veneno", "jugador")
        agenda.programar(100, rata)
        agenda.programar(66, veneno)
        agenda.programar(100, jugador)

        self.assertEqual(agenda.sacar_siguiente(), (66, 2, veneno))
        self.assertEqual(agenda.sacar_siguiente(), (100, 1, rata))
        self.assertEqual(agenda.sacar_siguiente(), (100, 3, jugador))
        self.assertTrue(agenda.esta_vacia())

    def test_ver_siguiente_no_saca(self):
        agenda = AgendaEventos()
        evento = Evento("accion", "jugador")
        agenda.programar(0, evento)
        self.assertEqual(agenda.ver_siguiente(), (0, 1, evento))
        self.assertEqual(agenda.tamano(), 1)

    def test_mismo_orden_siempre(self):
        def correr():
            agenda = AgendaEventos()
            for tiempo, objetivo in [(100, "a"), (100, "b"), (50, "c"), (100, "d"), (50, "e")]:
                agenda.programar(tiempo, Evento("accion", objetivo))
            return [agenda.sacar_siguiente()[2].objetivo for _ in range(5)]

        self.assertEqual(correr(), ["c", "e", "a", "b", "d"])
        self.assertEqual(correr(), correr())

    def test_agenda_vacia(self):
        agenda = AgendaEventos()
        self.assertTrue(agenda.esta_vacia())
        with self.assertRaises(IndexError):
            agenda.sacar_siguiente()


if __name__ == "__main__":
    unittest.main()