import random

from estructuras.vector_ordenado import VectorOrdenado
from modelo.agenda_eventos import AgendaEventos
from modelo.combate import atacar
from modelo.enemigo import Enemigo
from modelo.evento import Evento

EVENTO_ACCION = "accion"
# tiempo que tarda una acción con velocidad 100; a más velocidad, menos tiempo
TIEMPO_BASE_ACCION = 10000


def duracion_accion(velocidad):
    return max(1, TIEMPO_BASE_ACCION // velocidad)


class EstadoPartida:
    """Actores, agenda y azar de una partida. El random.Random es de la partida:
    misma semilla y mismas acciones dan siempre el mismo resultado."""

    def __init__(self, semilla, jugador):
        self.semilla = semilla
        self.azar = random.Random(semilla)
        self.agenda = AgendaEventos()
        self.jugador = jugador
        self.tiempo = 0
        self._enemigos = VectorOrdenado()   # instancia -> Enemigo
        self._suelo = VectorOrdenado()      # sala -> lista de ids de catálogo

    # ------------------------------------------------------------ enemigos

    def colocar_enemigo(self, instancia, ficha, sala):
        """Crea el Enemigo de una InstanciaEnemigo y programa su primera acción."""
        if self._enemigos.contiene(instancia.instancia):
            raise ValueError(f"ya existe el enemigo {instancia.instancia}")
        enemigo = Enemigo(instancia, ficha, sala)
        self._enemigos.insertar(enemigo.instancia, enemigo)
        if enemigo.esta_vivo():
            self.programar_accion(enemigo)
        return enemigo

    def programar_accion(self, enemigo):
        evento = Evento(EVENTO_ACCION, enemigo.id)
        self.agenda.programar(self.tiempo + duracion_accion(enemigo.velocidad), evento)
        enemigo.proximo_evento = evento

    def enemigo(self, instancia):
        return self._enemigos.buscar(instancia)

    def enemigos_en_sala(self, sala):
        """Enemigos vivos de la sala, ordenados por id de instancia."""
        return [e for _, e in self._enemigos if e.sala == sala and e.esta_vivo()]

    def suelo(self, sala):
        """Ids de catálogo de lo que hay soltado en la sala."""
        lista = self._suelo.buscar(sala)
        return [] if lista is None else list(lista)

    # -------------------------------------------------------------- combate

    def jugador_ataca(self, instancia=None):
        """El jugador ataca a un enemigo de su sala. Con más de uno hay que elegir
        por instancia; con uno solo se puede omitir."""
        if instancia is None:
            presentes = self.enemigos_en_sala(self.jugador.sala)
            if not presentes:
                raise ValueError("no hay enemigos en la sala")
            if len(presentes) > 1:
                raise ValueError("hay varios enemigos en la sala: hay que elegir cuál atacar")
            objetivo = presentes[0]
        else:
            objetivo = self._enemigos.buscar(instancia)
            if objetivo is None:
                raise ValueError(f"no existe el enemigo {instancia}")
        return self._atacar(self.jugador, objetivo)

    def ejecutar_siguiente(self):
        """Ejecuta el siguiente evento válido de la agenda (IndexError si no hay).
        Un enemigo en la sala del jugador lo ataca; en cualquier caso vuelve a
        programar su próxima acción. Devuelve el ResultadoAtaque, o None si no hubo ataque."""
        tiempo, _, evento = self.agenda.sacar_siguiente()
        self.tiempo = tiempo
        enemigo = self._enemigos.buscar(evento.objetivo)
        # un muerto no ejecuta nada, aunque su evento llegara hasta aquí
        if enemigo is None or not enemigo.esta_vivo():
            return None
        enemigo.proximo_evento = None
        resultado = None
        if evento.tipo == EVENTO_ACCION:
            if self.jugador.esta_vivo() and enemigo.sala == self.jugador.sala:
                resultado = self._atacar(enemigo, self.jugador)
            self.programar_accion(enemigo)
        return resultado

    def _atacar(self, atacante, defensor):
        resultado = atacar(atacante, defensor, self.azar)
        if resultado.murio and isinstance(defensor, Enemigo):
            self._morir(defensor)
        return resultado

    def _morir(self, enemigo):
        # no se busca en la agenda: se cancela su evento y se ignora al llegar
        if enemigo.proximo_evento is not None:
            self.agenda.cancelar(enemigo.proximo_evento)
            enemigo.proximo_evento = None
        lista = self._suelo.buscar(enemigo.sala)
        if lista is None:
            lista = []
            self._suelo.insertar(enemigo.sala, lista)
        for id_objeto in enemigo.suelta:
            lista.append(id_objeto)