import random

from estructuras.vector_ordenado import VectorOrdenado
from modelo.agenda_eventos import AgendaEventos
from modelo.combate import atacar
from modelo.enemigo import Enemigo
from modelo.evento import Evento
from modelo.movimiento import (MovimientoInvalido, NO_ES_TURNO, PUERTA_ABIERTA, PUERTA_CERRADA,
                               SALA_NO_DISPONIBLE, SIN_LLAVE, SIN_MAPA, SIN_SALIDA)

EVENTO_ACCION = "accion"
# un costo equivale a esa misma cantidad de tiempo a velocidad 100; a más velocidad, menos tiempo
VELOCIDAD_BASE = 100
COSTO_ACCION = 100          # acción de un enemigo (también su primera acción al activarse)
COSTO_MOVER = 100
COSTO_ABRIR_PUERTA = 100


def duracion_accion(velocidad, costo=COSTO_ACCION):
    return max(1, costo * VELOCIDAD_BASE // velocidad)


class EstadoPartida:
    """Actores, agenda y azar de una partida. El random.Random es de la partida:
    misma semilla y mismas acciones dan siempre el mismo resultado.

    El jugador también tiene su evento en la agenda: es su turno cuando ese evento
    es el siguiente. Usa el turno con mover_jugador / abrir_puerta, que programan
    el siguiente turno costo más adelante."""

    def __init__(self, semilla, jugador, esqueleto=None):
        self.semilla = semilla
        self.azar = random.Random(semilla)
        self.agenda = AgendaEventos()
        self.jugador = jugador
        self.esqueleto = esqueleto
        self.tiempo = 0
        self._enemigos = VectorOrdenado()   # instancia -> Enemigo
        self._suelo = VectorOrdenado()      # sala -> lista de ids de catálogo

    def iniciar(self):
        """Empieza la partida en t=0: el jugador tiene su primer turno y se activan
        los enemigos de su sala (hay que haberlos colocado antes)."""
        if self.jugador.proximo_evento is not None:
            raise ValueError("la partida ya empezó")
        self.tiempo = 0
        self._programar_turno_jugador(0)
        self.activar_enemigos(self.jugador.sala)

    # ------------------------------------------------------------ enemigos

    def colocar_enemigo(self, instancia, ficha, sala):
        """Crea el Enemigo de una InstanciaEnemigo. Queda inactivo: no actúa hasta
        que se active (iniciar() o la entrada del jugador a su sala)."""
        if self._enemigos.contiene(instancia.instancia):
            raise ValueError(f"ya existe el enemigo {instancia.instancia}")
        enemigo = Enemigo(instancia, ficha, sala)
        self._enemigos.insertar(enemigo.instancia, enemigo)
        return enemigo

    def activar_enemigos(self, sala):
        """Activa los enemigos vivos de la sala que sigan inactivos, por orden de
        instancia, y programa su primera acción (costo 100). Los que ya están
        activos no se tocan, estén en la sala que estén."""
        activados = []
        for enemigo in self.enemigos_en_sala(sala):
            if not enemigo.activo:
                enemigo.activo = True
                self.programar_accion(enemigo)
                activados.append(enemigo)
        return activados

    def programar_accion(self, enemigo, costo=COSTO_ACCION):
        evento = Evento(EVENTO_ACCION, enemigo.id)
        self.agenda.programar(self.tiempo + duracion_accion(enemigo.velocidad, costo), evento)
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

    # ---------------------------------------------------------------- turno

    def es_turno_del_jugador(self):
        if self.jugador.proximo_evento is None or self.agenda.esta_vacia():
            return False
        return self.agenda.ver_siguiente()[2] is self.jugador.proximo_evento

    def avanzar_hasta_turno_jugador(self):
        """Ejecuta los eventos de los enemigos hasta que le toque al jugador (o muera).
        Devuelve los ResultadoAtaque ocurridos mientras tanto."""
        if self.jugador.proximo_evento is None:
            raise ValueError("el jugador no tiene turno: falta iniciar() o murió")
        resultados = []
        while self.jugador.proximo_evento is not None and not self.es_turno_del_jugador():
            resultado = self.ejecutar_siguiente()
            if resultado is not None:
                resultados.append(resultado)
        if self.es_turno_del_jugador():
            self.tiempo = self.agenda.ver_siguiente()[0]
        return resultados

    def _programar_turno_jugador(self, duracion):
        evento = Evento(EVENTO_ACCION, self.jugador.id)
        self.agenda.programar(self.tiempo + duracion, evento)
        self.jugador.proximo_evento = evento

    def _gastar_turno(self, costo):
        # a igual tiempo gana la menor secuencia: como el siguiente turno se programa
        # antes de activar enemigos, el jugador actúa antes que el grupo recién activado
        tiempo, _, _ = self.agenda.sacar_siguiente()
        self.tiempo = tiempo
        self._programar_turno_jugador(duracion_accion(self.jugador.velocidad, costo))

    # ------------------------------------------------------ mapa y puertas

    def mover_jugador(self, direccion):
        """Mueve al jugador por una salida (N, S, E, O) a la sala vecina. Cuesta
        COSTO_MOVER. Si la puerta está cerrada hay que abrirla antes (otra acción).
        Al entrar se activan los enemigos de la sala destino. Devuelve la sala nueva;
        si no se puede lanza MovimientoInvalido y no pasa nada."""
        self._exigir_turno()
        salida = self._salida(direccion)
        if self.esqueleto.obtener(salida.sala_destino) is None:
            raise MovimientoInvalido(SALA_NO_DISPONIBLE,
                                     f"la sala {salida.sala_destino} no está disponible")
        if not self.esqueleto.puede_atravesar(self.jugador.sala, direccion):
            raise MovimientoInvalido(PUERTA_CERRADA, "la puerta está cerrada: hay que abrirla antes")
        self._gastar_turno(COSTO_MOVER)
        self.jugador.sala = salida.sala_destino
        self.activar_enemigos(salida.sala_destino)
        return salida.sala_destino

    def abrir_puerta(self, direccion):
        """Abre la puerta cerrada de esa salida si el jugador tiene su llave (la llave
        no se gasta). Cuesta COSTO_ABRIR_PUERTA. Se abre para las dos salas."""
        self._exigir_turno()
        self._salida(direccion)
        puerta = self.esqueleto.puerta(self.jugador.sala, direccion)
        if puerta.esta_abierta():
            raise MovimientoInvalido(PUERTA_ABIERTA, "la puerta ya está abierta")
        if not self.jugador.puede_abrir(puerta):
            raise MovimientoInvalido(SIN_LLAVE, "falta la llave de esta puerta")
        self._gastar_turno(COSTO_ABRIR_PUERTA)
        puerta.abrir()
        return puerta

    def _exigir_turno(self):
        if not self.es_turno_del_jugador():
            raise MovimientoInvalido(NO_ES_TURNO, "no es el turno del jugador")

    def _salida(self, direccion):
        if self.esqueleto is None:
            raise MovimientoInvalido(SIN_MAPA, "la partida no tiene mapa")
        salida = self.esqueleto.salida(self.jugador.sala, direccion)
        if salida is None:
            raise MovimientoInvalido(SIN_SALIDA, f"no hay salida hacia {direccion}")
        return salida

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
        programar su próxima acción. Devuelve el ResultadoAtaque, o None si no hubo ataque.
        Si el siguiente evento es el turno del jugador, no lo ejecuta (ValueError)."""
        tiempo, _, evento = self.agenda.ver_siguiente()
        if evento is self.jugador.proximo_evento:
            raise ValueError("es el turno del jugador")
        self.agenda.sacar_siguiente()
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
        if resultado.murio:
            self._morir(defensor)
        return resultado

    def _morir(self, actor):
        # no se busca en la agenda: se cancela su evento y se ignora al llegar
        if actor.proximo_evento is not None:
            self.agenda.cancelar(actor.proximo_evento)
            actor.proximo_evento = None
        if isinstance(actor, Enemigo):
            lista = self._suelo.buscar(actor.sala)
            if lista is None:
                lista = []
                self._suelo.insertar(actor.sala, lista)
            for id_objeto in actor.suelta:
                lista.append(id_objeto)