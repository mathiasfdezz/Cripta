import random

from estructuras.vector_ordenado import VectorOrdenado
from modelo.agenda_eventos import AgendaEventos
from modelo.combate import atacar, puede_atacar
from modelo.enemigo import ERRANTE, RASTREADOR, Enemigo
from modelo.evento import Evento
from modelo.historial import Historial
from modelo.movimiento import (CONTENIDO_PENDIENTE, INVENTARIO_LLENO, MovimientoInvalido,
                               NADA_QUE_DESHACER, NADA_QUE_RECOGER, NO_EQUIPABLE, NO_ES_TURNO,
                               NO_USABLE, PARTIDA_TERMINADA, PUERTA_ABIERTA, PUERTA_CERRADA,
                               SALA_NO_DISPONIBLE, SIN_ENEMIGO, SIN_LLAVE, SIN_MAPA, SIN_OBJETO,
                               SIN_PERGAMINO, SIN_SALIDA)
from modelo.rastro import Rastro

EVENTO_ACCION = "accion"
EVENTO_FIN_VELOCIDAD = "fin_velocidad"
EVENTO_APAGAR_ANTORCHA = "apagar_antorcha"

# un costo equivale a esa misma cantidad de tiempo a velocidad 100; a más velocidad, menos tiempo
VELOCIDAD_BASE = 100
COSTO_ACCION = 100          # acción de un enemigo (también su primera acción al activarse)
COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_ABRIR_PUERTA = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25

EN_CURSO = "en_curso"
VICTORIA = "victoria"
DERROTA = "derrota"

CLASE_PERGAMINO = "pergamino_retroceso"
CLASES_EQUIPABLES = ("arma", "armadura")
CLASES_USABLES = ("pocion", "antidoto", "antorcha")


def duracion_accion(velocidad, costo=COSTO_ACCION):
    return max(1, costo * VELOCIDAD_BASE // velocidad)


class EstadoPartida:
    """Actores, agenda y azar de una partida. El random.Random es de la partida:
    misma semilla y mismas acciones dan siempre el mismo resultado.

    El jugador también tiene su evento en la agenda: es su turno cuando ese evento
    es el siguiente. Cada acción suya gasta su turno y programa el siguiente
    costo más adelante. Las acciones rechazadas lanzan MovimientoInvalido y no
    cambian nada.

    Todo cambio de estado pasa por el historial para que el pergamino de
    retroceso pueda deshacerlo (se guarda el valor anterior, no una copia)."""

    def __init__(self, semilla, jugador, esqueleto=None, obtener_ficha=None):
        self.semilla = semilla
        self.azar = random.Random(semilla)
        self.historial = Historial()
        self.agenda = AgendaEventos()
        self.agenda.registrar = self.historial.registrar
        self.jugador = jugador
        self.esqueleto = esqueleto
        self.rastro = None if esqueleto is None else Rastro(esqueleto)
        self.tiempo = 0
        self.resultado = EN_CURSO
        self.acciones = 0
        self.enemigos_derrotados = 0
        self.antorcha_hasta = None
        # si es True, el jugador no puede entrar a una sala cuyo contenido no se conoce
        self.controlar_contenido = False
        self.sala_salida = None
        self.llave_salida = None
        self._puerta_salida_abierta = False
        self._obtener_ficha = obtener_ficha
        self._enemigos = VectorOrdenado()   # instancia -> Enemigo
        self._suelo = VectorOrdenado()      # sala -> lista de ids de catálogo
        self._trampas = VectorOrdenado()    # sala -> lista de InstanciaTrampa
        self._cargadas = VectorOrdenado()   # sala -> True cuando su contenido ya está

    def configurar_salida(self, sala_salida, llave_salida):
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida

    def iniciar(self):
        """Empieza la partida en t=0: el jugador tiene su primer turno y se activan
        los enemigos de su sala (hay que haberlos colocado antes)."""
        if self.jugador.proximo_evento is not None:
            raise ValueError("la partida ya empezó")
        self.tiempo = 0
        self._programar_turno_jugador(0)
        self._marcar_rastro()
        self.activar_enemigos(self.jugador.sala)

    def terminada(self):
        return self.resultado != EN_CURSO

    # ------------------------------------------------------------ contenido

    def cargar_contenido(self, contenido):
        """Incorpora un ContenidoSala (DTO). Llegar datos no es una acción del juego:
        no se deshace con el pergamino y no activa enemigos."""
        if self._cargadas.contiene(contenido.sala):
            return
        with self.historial.sin_registrar():
            for instancia in contenido.enemigos:
                if not self._enemigos.contiene(instancia.instancia):
                    self.colocar_enemigo(instancia, self._obtener_ficha(instancia.tipo),
                                         contenido.sala)
            for id_objeto in contenido.objetos:
                self._suelo_agregar(contenido.sala, id_objeto)
            self._trampas.insertar(contenido.sala, list(contenido.trampas))
            self._cargadas.insertar(contenido.sala, True)

    def contenido_cargado(self, sala):
        return self._cargadas.contiene(sala)

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
                self._asignar(enemigo, "activo", True)
                self.programar_accion(enemigo)
                activados.append(enemigo)
        return activados

    def programar_accion(self, enemigo, costo=COSTO_ACCION):
        evento = Evento(EVENTO_ACCION, enemigo.id)
        self.agenda.programar(self.tiempo + duracion_accion(enemigo.velocidad, costo), evento)
        self._asignar(enemigo, "proximo_evento", evento)

    def enemigo(self, instancia):
        return self._enemigos.buscar(instancia)

    def enemigos_en_sala(self, sala):
        """Enemigos vivos de la sala, ordenados por id de instancia."""
        return [e for _, e in self._enemigos if e.sala == sala and e.esta_vivo()]

    def suelo(self, sala):
        """Ids de catálogo de lo que hay en el suelo de la sala."""
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
            self._asignar(self, "tiempo", self.agenda.ver_siguiente()[0])
        return resultados

    def _programar_turno_jugador(self, duracion):
        evento = Evento(EVENTO_ACCION, self.jugador.id)
        self.agenda.programar(self.tiempo + duracion, evento)
        self._asignar(self.jugador, "proximo_evento", evento)

    def _gastar_turno(self, costo):
        # aquí empieza una acción del jugador: lo que cambie desde ahora hasta su
        # siguiente decisión es lo que revierte un pergamino
        self.historial.abrir_intervalo()
        estado_azar = self.azar.getstate()
        self.historial.registrar(lambda: self.azar.setstate(estado_azar))
        self._asignar(self, "acciones", self.acciones + 1)
        # a igual tiempo gana la menor secuencia: como el siguiente turno se programa
        # antes de activar enemigos, el jugador actúa antes que el grupo recién activado
        tiempo, _, _ = self.agenda.sacar_siguiente()
        self._asignar(self, "tiempo", tiempo)
        self._programar_turno_jugador(duracion_accion(self.jugador.velocidad, costo))

    def _exigir_turno(self):
        if self.terminada():
            raise MovimientoInvalido(PARTIDA_TERMINADA, "la partida ya terminó")
        if not self.es_turno_del_jugador():
            raise MovimientoInvalido(NO_ES_TURNO, "no es el turno del jugador")

    # ------------------------------------------------------ mapa y puertas

    def mover_jugador(self, direccion):
        """Mueve al jugador por una salida (N, S, E, O) a la sala vecina. Cuesta
        COSTO_MOVER. Si la puerta está cerrada hay que abrirla antes (otra acción).
        Al entrar se activan los enemigos de la sala destino. Devuelve la sala nueva."""
        self._exigir_turno()
        salida = self._salida(direccion)
        destino = salida.sala_destino
        if self.esqueleto.obtener(destino) is None:
            raise MovimientoInvalido(SALA_NO_DISPONIBLE, f"la sala {destino} no está disponible")
        if self.controlar_contenido and not self.contenido_cargado(destino):
            raise MovimientoInvalido(CONTENIDO_PENDIENTE,
                                     f"el contenido de la sala {destino} aún no llegó")
        if not self.esqueleto.puede_atravesar(self.jugador.sala, direccion):
            raise MovimientoInvalido(PUERTA_CERRADA, "la puerta está cerrada: hay que abrirla antes")
        self._gastar_turno(COSTO_MOVER)
        self._asignar(self.jugador, "sala", destino)
        self._marcar_rastro()
        self.activar_enemigos(destino)
        if destino == self.sala_salida and self._puerta_salida_abierta:
            self._asignar(self, "resultado", VICTORIA)
            self._cancelar_turno_jugador()
        return destino

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
        self._marcar_rastro()
        self._recordar(puerta, "cerrada")
        self._recordar(puerta, "_tocada")
        puerta.abrir()
        if self.llave_salida is not None and puerta.llave == self.llave_salida:
            self._asignar(self, "_puerta_salida_abierta", True)
        return puerta

    def _salida(self, direccion):
        if self.esqueleto is None:
            raise MovimientoInvalido(SIN_MAPA, "la partida no tiene mapa")
        salida = self.esqueleto.salida(self.jugador.sala, direccion)
        if salida is None:
            raise MovimientoInvalido(SIN_SALIDA, f"no hay salida hacia {direccion}")
        return salida

    def _marcar_rastro(self):
        # cada acción del jugador refresca el rastro de la sala donde queda
        if self.rastro is None:
            return
        sala = self.jugador.sala
        anterior = self.rastro.tiempo_en(sala)
        self.rastro.marcar(sala, self.tiempo)
        self.historial.registrar(lambda: self.rastro.marcar(sala, anterior))

    # ------------------------------------------------------------- objetos

    def esperar(self):
        self._exigir_turno()
        self._gastar_turno(COSTO_ESPERAR)
        self._marcar_rastro()

    def recoger(self, id_objeto=None):
        """Recoge un objeto del suelo de la sala. Si hay de varios tipos hay que decir
        cuál. Con el inventario lleno se rechaza sin gastar tiempo. Cuesta 25."""
        self._exigir_turno()
        sala = self.jugador.sala
        en_suelo = self.suelo(sala)
        if not en_suelo:
            raise MovimientoInvalido(NADA_QUE_RECOGER, "no hay nada en el suelo")
        if id_objeto is None:
            for otro in en_suelo:
                if otro != en_suelo[0]:
                    raise MovimientoInvalido(NADA_QUE_RECOGER,
                                             "hay varios objetos: indica cuál recoger")
            id_objeto = en_suelo[0]
        elif id_objeto not in en_suelo:
            raise MovimientoInvalido(NADA_QUE_RECOGER, f"{id_objeto} no está en el suelo")
        if self.jugador.inventario.esta_lleno():
            raise MovimientoInvalido(INVENTARIO_LLENO, "el inventario está lleno: suelta algo antes")
        ficha = self._obtener_ficha(id_objeto)
        self._gastar_turno(COSTO_RECOGER)
        self._marcar_rastro()
        # los pergaminos quedan fuera del retroceso
        if ficha.clase == CLASE_PERGAMINO:
            with self.historial.sin_registrar():
                self._suelo_quitar(sala, id_objeto)
                self._inventario_agregar(ficha)
        else:
            self._suelo_quitar(sala, id_objeto)
            self._inventario_agregar(ficha)
        return ficha

    def soltar(self):
        """Suelta el objeto que se está viendo en el inventario. Cuesta 25."""
        self._exigir_turno()
        ficha = self._objeto_actual()
        self._gastar_turno(COSTO_SOLTAR)
        self._marcar_rastro()
        if ficha.clase == CLASE_PERGAMINO:
            with self.historial.sin_registrar():
                self._inventario_quitar_actual()
                self._suelo_agregar(self.jugador.sala, ficha.id)
        else:
            self._inventario_quitar_actual()
            self._suelo_agregar(self.jugador.sala, ficha.id)
        return ficha

    def equipar(self):
        """Equipa el arma o armadura que se está viendo: pasa al frente del
        inventario y suma su bonus. Cuesta 50."""
        self._exigir_turno()
        ficha = self._objeto_actual()
        if ficha.clase not in CLASES_EQUIPABLES:
            raise MovimientoInvalido(NO_EQUIPABLE, f"{ficha.nombre} no se puede equipar")
        self._gastar_turno(COSTO_EQUIPAR)
        self._marcar_rastro()
        inventario = self.jugador.inventario
        nodo = inventario.actual
        previo = nodo.anterior
        self._recordar_inventario()
        inventario.equipar_actual()
        self.historial.registrar(lambda: self._volver_a_su_lugar(nodo, previo))
        return ficha

    def usar(self):
        """Usa la poción, antídoto o antorcha que se está viendo; se consume. Cuesta 50.
        Los pergaminos se usan con deshacer()."""
        self._exigir_turno()
        ficha = self._objeto_actual()
        if ficha.clase not in CLASES_USABLES:
            raise MovimientoInvalido(NO_USABLE, f"{ficha.nombre} no se puede usar así")
        self._gastar_turno(COSTO_USAR)
        self._marcar_rastro()
        self._inventario_quitar_actual()
        if ficha.clase == "pocion":
            if ficha.cura:
                vida = min(self.jugador.vida_max, self.jugador.vida + ficha.cura)
                self._asignar(self.jugador, "vida", vida)
            if ficha.modificador_velocidad and ficha.duracion:
                self._cambiar_velocidad_jugador(self.jugador.velocidad + ficha.modificador_velocidad)
                self.agenda.programar(self.tiempo + ficha.duracion,
                                      Evento(EVENTO_FIN_VELOCIDAD, self.jugador.id,
                                             ficha.modificador_velocidad))
        elif ficha.clase == "antorcha":
            self._asignar(self, "antorcha_hasta", self.tiempo + ficha.duracion)
            self.agenda.programar(self.antorcha_hasta,
                                  Evento(EVENTO_APAGAR_ANTORCHA, self.jugador.id))
        # antídoto: cancela el veneno activo; el contrato del API no trae veneno todavía
        return ficha

    def deshacer(self):
        """Usa un pergamino de retroceso: vuelve al estado anterior a la última acción
        del jugador. No gasta tiempo ni cuenta como acción. El pergamino se consume
        y la cantidad de pergaminos nunca se revierte."""
        self._exigir_turno()
        inventario = self.jugador.inventario
        if inventario.cantidad_pergaminos() == 0:
            raise MovimientoInvalido(SIN_PERGAMINO, "no tienes pergaminos de retroceso")
        if not self.historial.deshacer():
            raise MovimientoInvalido(NADA_QUE_DESHACER, "no hay acciones para deshacer")
        with self.historial.sin_registrar():
            inventario.consumir_primero_de_clase(CLASE_PERGAMINO)

    def _objeto_actual(self):
        ficha = self.jugador.inventario.obtener_actual()
        if ficha is None:
            raise MovimientoInvalido(SIN_OBJETO, "no hay un objeto seleccionado en el inventario")
        return ficha

    def _cambiar_velocidad_jugador(self, nueva):
        anterior = self.jugador.velocidad
        nueva = max(1, nueva)
        self._asignar(self.jugador, "velocidad", nueva)
        evento = self.jugador.proximo_evento
        if evento is not None and evento.en_agenda and not evento.cancelado:
            _, reprogramado = self.agenda.cambiar_velocidad(evento, self.tiempo, anterior, nueva)
            self._asignar(self.jugador, "proximo_evento", reprogramado)

    # -------------------------------------------------------------- combate

    def jugador_ataca(self, instancia=None):
        """El jugador ataca a un enemigo de su sala en su turno. Cuesta COSTO_ATACAR.
        Con más de un enemigo hay que elegir por instancia; con uno solo se puede
        omitir. Si no se puede atacar no se gasta el turno."""
        self._exigir_turno()
        if instancia is None:
            presentes = self.enemigos_en_sala(self.jugador.sala)
            if not presentes:
                raise MovimientoInvalido(SIN_ENEMIGO, "no hay enemigos en la sala")
            if len(presentes) > 1:
                raise MovimientoInvalido(SIN_ENEMIGO,
                                         "hay varios enemigos en la sala: hay que elegir cuál atacar")
            objetivo = presentes[0]
        else:
            objetivo = self._enemigos.buscar(instancia)
            if objetivo is None:
                raise MovimientoInvalido(SIN_ENEMIGO, f"no existe el enemigo {instancia}")
        if not puede_atacar(self.jugador, objetivo):
            raise MovimientoInvalido(SIN_ENEMIGO, f"no se puede atacar a {objetivo.id}: "
                                                  "debe estar vivo y en la misma sala")
        self._gastar_turno(COSTO_ATACAR)
        self._marcar_rastro()
        return self._atacar(self.jugador, objetivo)

    def ejecutar_siguiente(self):
        """Ejecuta el siguiente evento válido de la agenda (IndexError si no hay).
        Un enemigo en la sala del jugador lo ataca; si no, aplica su comportamiento.
        Devuelve el ResultadoAtaque, o None si no hubo ataque.
        Si el siguiente evento es el turno del jugador, no lo ejecuta (ValueError)."""
        tiempo, _, evento = self.agenda.ver_siguiente()
        if evento is self.jugador.proximo_evento:
            raise ValueError("es el turno del jugador")
        self.agenda.sacar_siguiente()
        self._asignar(self, "tiempo", tiempo)
        if evento.tipo == EVENTO_FIN_VELOCIDAD:
            self._cambiar_velocidad_jugador(self.jugador.velocidad - evento.dato)
            return None
        if evento.tipo == EVENTO_APAGAR_ANTORCHA:
            if self.antorcha_hasta is not None and self.antorcha_hasta <= self.tiempo:
                self._asignar(self, "antorcha_hasta", None)
            return None
        enemigo = self._enemigos.buscar(evento.objetivo)
        # un muerto no ejecuta nada, aunque su evento llegara hasta aquí
        if enemigo is None or not enemigo.esta_vivo():
            return None
        self._asignar(enemigo, "proximo_evento", None)
        resultado = None
        if evento.tipo == EVENTO_ACCION:
            if self.jugador.esta_vivo() and enemigo.sala == self.jugador.sala:
                resultado = self._atacar(enemigo, self.jugador)
            else:
                self._comportarse(enemigo)
            self.programar_accion(enemigo)
        return resultado

    def _comportarse(self, enemigo):
        """Lo que hace un enemigo que no comparte sala con el jugador. Moverse o
        esperar cuestan lo mismo (100), así que la próxima acción no cambia."""
        if self.rastro is None:
            return
        if enemigo.comportamiento == ERRANTE:
            opciones = self.rastro.salidas_abiertas(enemigo.sala)
            if opciones:
                self._asignar(enemigo, "sala", opciones[self.azar.randrange(len(opciones))])
        elif enemigo.comportamiento == RASTREADOR:
            destino = self.rastro.sala_mas_fresca(enemigo.sala, self.tiempo)
            if destino is not None:
                self._asignar(enemigo, "sala", destino)
        # guardián: espera, nunca deja su sala

    def _atacar(self, atacante, defensor):
        self._recordar(defensor, "vida")
        resultado = atacar(atacante, defensor, self.azar)
        if resultado.murio:
            self._morir(defensor)
        return resultado

    def _morir(self, actor):
        # no se busca en la agenda: se cancela su evento y se ignora al llegar
        if actor.proximo_evento is not None:
            self.agenda.cancelar(actor.proximo_evento)
            self._asignar(actor, "proximo_evento", None)
        if isinstance(actor, Enemigo):
            self._asignar(self, "enemigos_derrotados", self.enemigos_derrotados + 1)
            for id_objeto in actor.suelta:
                self._suelo_agregar(actor.sala, id_objeto)
        else:
            self._asignar(self, "resultado", DERROTA)

    def _cancelar_turno_jugador(self):
        if self.jugador.proximo_evento is not None:
            self.agenda.cancelar(self.jugador.proximo_evento)
            self._asignar(self.jugador, "proximo_evento", None)

    # -------------------------------------- cambios que se pueden deshacer

    def _asignar(self, objeto, atributo, valor):
        self._recordar(objeto, atributo)
        setattr(objeto, atributo, valor)

    def _recordar(self, objeto, atributo):
        anterior = getattr(objeto, atributo)
        self.historial.registrar(lambda: setattr(objeto, atributo, anterior))

    def _suelo_agregar(self, sala, id_objeto):
        lista = self._suelo.buscar(sala)
        if lista is None:
            lista = []
            self._suelo.insertar(sala, lista)
        lista.append(id_objeto)
        self.historial.registrar(lambda: lista.pop())

    def _suelo_quitar(self, sala, id_objeto):
        lista = self._suelo.buscar(sala)
        posicion = lista.index(id_objeto)
        del lista[posicion]
        self.historial.registrar(lambda: lista.insert(posicion, id_objeto))

    def _recordar_inventario(self):
        inventario = self.jugador.inventario
        for atributo in ("actual", "_nodo_arma", "_nodo_armadura"):
            self._recordar(inventario, atributo)

    def _inventario_agregar(self, ficha):
        inventario = self.jugador.inventario
        self._recordar_inventario()
        inventario.recoger(ficha)
        nodo = inventario.lista.cola
        self.historial.registrar(lambda: inventario.lista.eliminar_nodo(nodo))

    def _inventario_quitar_actual(self):
        inventario = self.jugador.inventario
        nodo = inventario.actual
        previo = nodo.anterior
        self._recordar_inventario()
        inventario.soltar_actual()
        self.historial.registrar(lambda: inventario.lista.enlazar_despues(previo, nodo))

    def _volver_a_su_lugar(self, nodo, previo):
        lista = self.jugador.inventario.lista
        lista.eliminar_nodo(nodo)
        lista.enlazar_despues(previo, nodo)
