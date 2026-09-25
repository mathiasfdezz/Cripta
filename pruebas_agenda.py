from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento


def prueba_secuencia_creciente():
    agenda = AgendaEventos()
    s1 = agenda.programar(100, Evento("accion", "jugador"))
    s2 = agenda.programar(50, Evento("accion", "e-201"))
    s3 = agenda.programar(100, Evento("veneno", "jugador"))
    assert (s1, s2, s3) == (1, 2, 3)


def prueba_empate_lo_decide_la_secuencia():
    agenda = AgendaEventos()
    rata = Evento("accion", "e-201")
    jugador = Evento("accion", "jugador")
    veneno = Evento("veneno", "jugador")
    agenda.programar(100, rata)
    agenda.programar(66, veneno)
    agenda.programar(100, jugador)

    assert agenda.sacar_siguiente() == (66, 2, veneno)
    assert agenda.sacar_siguiente() == (100, 1, rata)
    assert agenda.sacar_siguiente() == (100, 3, jugador)
    assert agenda.esta_vacia()


def prueba_ver_siguiente_no_saca():
    agenda = AgendaEventos()
    evento = Evento("accion", "jugador")
    agenda.programar(0, evento)
    assert agenda.ver_siguiente() == (0, 1, evento)
    assert agenda.tamano() == 1


def prueba_mismo_orden_siempre():
    def correr():
        agenda = AgendaEventos()
        for tiempo, objetivo in [(100, "a"), (100, "b"), (50, "c"), (100, "d"), (50, "e")]:
            agenda.programar(tiempo, Evento("accion", objetivo))
        return [agenda.sacar_siguiente()[2].objetivo for _ in range(5)]

    assert correr() == ["c", "e", "a", "b", "d"]
    assert correr() == correr()


def prueba_agenda_vacia():
    agenda = AgendaEventos()
    assert agenda.esta_vacia()
    try:
        agenda.sacar_siguiente()
        assert False, "debió lanzar IndexError"
    except IndexError:
        pass


if __name__ == "__main__":
    pruebas = [prueba_secuencia_creciente, prueba_empate_lo_decide_la_secuencia,
               prueba_ver_siguiente_no_saca, prueba_mismo_orden_siempre, prueba_agenda_vacia]
    for prueba in pruebas:
        prueba()
        print(f"ok  {prueba.__name__}")
