import random

from bench.agenda_lista import AgendaLista
from bench.cronometro import medir_us
from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento

OPERACIONES = 2000


def _llenar(agenda, n, azar):
    for i in range(n):
        agenda.programar(azar.randint(0, 10000), Evento("accion", f"e-{i}"))


def _ciclo(agenda, azar):
    # como en el juego: sale el siguiente y vuelve a programarse más adelante
    def paso(_):
        tiempo, _, evento = agenda.sacar_siguiente()
        agenda.programar(tiempo + azar.randint(1, 200), evento)
    return paso


def principal():
    print("== Agenda: sacar el siguiente y reprogramarlo (us por operacion) ==")
    print("%8s %12s %12s %10s" % ("eventos", "heap", "lista", "lista/heap"))
    for n in (100, 300, 1000, 3000):
        resultados = []
        for agenda in (AgendaEventos(), AgendaLista()):
            azar = random.Random(n)
            _llenar(agenda, n, azar)
            resultados.append(medir_us(_ciclo(agenda, azar), OPERACIONES))
        heap, lista = resultados
        print("%8d %12.2f %12.2f %10.1f" % (n, heap, lista, lista / heap))


if __name__ == "__main__":
    principal()