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

    def test_cancelar_un_evento(self):
        agenda = AgendaEventos()
        a = Evento("accion", "a")
        b = Evento("accion", "b")
        c = Evento("accion", "c")
        agenda.programar(10, a)
        agenda.programar(20, b)
        agenda.programar(30, c)

        self.assertTrue(agenda.cancelar(a))
        self.assertTrue(a.cancelado)
        self.assertEqual(agenda.tamano(), 2)
        self.assertEqual(agenda.ver_siguiente(), (20, 2, b))
        self.assertEqual(agenda.sacar_siguiente(), (20, 2, b))
        self.assertEqual(agenda.sacar_siguiente(), (30, 3, c))
        self.assertTrue(agenda.esta_vacia())

    def test_cancelar_dos_veces_o_evento_ya_sacado(self):
        agenda = AgendaEventos()
        a = Evento("accion", "a")
        b = Evento("accion", "b")
        agenda.programar(10, a)
        agenda.programar(20, b)
        self.assertTrue(agenda.cancelar(b))
        self.assertFalse(agenda.cancelar(b))
        self.assertEqual(agenda.tamano(), 1)
        agenda.sacar_siguiente()
        self.assertFalse(agenda.cancelar(a))
        self.assertFalse(a.cancelado)
        self.assertTrue(agenda.esta_vacia())

    def test_varios_cancelados_se_ignoran(self):
        agenda = AgendaEventos()
        eventos = [Evento("accion", str(i)) for i in range(6)]
        for i, evento in enumerate(eventos):
            agenda.programar(10 * (i + 1), evento)
        for i in (0, 1, 3, 4):
            agenda.cancelar(eventos[i])

        self.assertEqual(agenda.tamano(), 2)
        self.assertEqual(agenda.sacar_siguiente()[2].objetivo, "2")
        self.assertEqual(agenda.sacar_siguiente()[2].objetivo, "5")
        self.assertTrue(agenda.esta_vacia())
        self.assertEqual(agenda.tamano(), 0)

    def test_cancelado_en_medio_del_heap_se_ignora_al_llegar(self):
        agenda = AgendaEventos()
        a = Evento("accion", "a")
        b = Evento("accion", "b")
        c = Evento("accion", "c")
        agenda.programar(10, a)
        agenda.programar(20, b)
        agenda.programar(30, c)
        agenda.cancelar(b)
        self.assertEqual(agenda.sacar_siguiente()[2], a)
        self.assertEqual(agenda.sacar_siguiente()[2], c)

    def test_todos_cancelados(self):
        agenda = AgendaEventos()
        eventos = [Evento("accion", str(i)) for i in range(4)]
        for i, evento in enumerate(eventos):
            agenda.programar(5 * i, evento)
        for evento in eventos:
            agenda.cancelar(evento)

        self.assertEqual(agenda.tamano(), 0)
        self.assertTrue(agenda.esta_vacia())
        with self.assertRaises(IndexError):
            agenda.ver_siguiente()
        with self.assertRaises(IndexError):
            agenda.sacar_siguiente()

    def test_reprogramar_cancela_la_version_anterior(self):
        agenda = AgendaEventos()
        a = Evento("accion", "a")
        b = Evento("accion", "b")
        agenda.programar(10, a)
        agenda.programar(20, b)

        secuencia, nuevo = agenda.reprogramar(a, 20)

        self.assertTrue(a.cancelado)
        self.assertFalse(nuevo.cancelado)
        self.assertIsNot(nuevo, a)
        self.assertEqual((nuevo.tipo, nuevo.objetivo), ("accion", "a"))
        self.assertEqual(secuencia, 3)
        self.assertEqual(nuevo.secuencia, 3)
        self.assertEqual(agenda.tamano(), 2)
        # mismo tiempo que b: b va primero porque tiene menor secuencia
        self.assertEqual(agenda.sacar_siguiente(), (20, 2, b))
        self.assertEqual(agenda.sacar_siguiente(), (20, 3, nuevo))
        self.assertTrue(agenda.esta_vacia())

    def test_reprogramar_a_un_tiempo_anterior(self):
        agenda = AgendaEventos()
        a = Evento("accion", "a")
        b = Evento("accion", "b")
        agenda.programar(50, a)
        agenda.programar(20, b)
        _, nuevo = agenda.reprogramar(a, 5)
        self.assertEqual(agenda.sacar_siguiente(), (5, 3, nuevo))
        self.assertEqual(agenda.sacar_siguiente(), (20, 2, b))
        self.assertTrue(agenda.esta_vacia())

    def test_calculo_tiempo_por_cambio_de_velocidad(self):
        calcular = AgendaEventos.calcular_tiempo_por_velocidad
        # ejemplo del enunciado: restante 100 con el doble de velocidad -> 50
        self.assertEqual(calcular(200, 100, 100, 200), 150)
        # velocidad a la mitad: el restante se duplica
        self.assertEqual(calcular(200, 100, 100, 50), 300)
        # division entera hacia abajo: 100 * 100 // 150 = 66
        self.assertEqual(calcular(200, 100, 100, 150), 166)
        # el restante nunca baja de 1
        self.assertEqual(calcular(101, 100, 100, 1000), 101)
        self.assertEqual(calcular(100, 100, 100, 200), 101)

    def test_velocidad_invalida(self):
        with self.assertRaises(ValueError):
            AgendaEventos.calcular_tiempo_por_velocidad(200, 100, 100, 0)
        with self.assertRaises(ValueError):
            AgendaEventos.calcular_tiempo_por_velocidad(200, 100, 0, 100)

    def test_cambiar_velocidad_reprograma_con_nueva_secuencia(self):
        agenda = AgendaEventos()
        rata = Evento("accion", "e-201")
        otro = Evento("accion", "jugador")
        agenda.programar(200, rata)
        agenda.programar(150, otro)

        secuencia, nuevo = agenda.cambiar_velocidad(rata, 100, 100, 200)

        self.assertTrue(rata.cancelado)
        self.assertEqual(nuevo.tiempo_siguiente, 150)
        self.assertEqual(secuencia, 3)
        # empate en 150: el de menor secuencia (otro) sale antes
        self.assertEqual(agenda.sacar_siguiente(), (150, 2, otro))
        self.assertEqual(agenda.sacar_siguiente(), (150, 3, nuevo))
        self.assertTrue(agenda.esta_vacia())

    def test_cambiar_velocidad_de_evento_no_programado(self):
        agenda = AgendaEventos()
        with self.assertRaises(ValueError):
            agenda.cambiar_velocidad(Evento("accion", "a"), 0, 100, 200)


if __name__ == "__main__":
    unittest.main()