import os

from adaptadores.guardado_binario import (NINGUNO, ArchivoGuardado, DatosCabecera, DatosJugador,
                                          DatosSala, GuardadoIncompatible, guardar)
from dtos.instancia_enemigo import InstanciaEnemigo
from modelo.estado_partida import EstadoPartida
from modelo.evento import Evento
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.trampa import Trampa


class GuardadoPartida:
    """Convierte una partida en curso en el archivo binario y al revés.
    El modelo no sabe de archivos: este adaptador lee y arma el estado con su API."""

    @staticmethod
    def guardar(ruta, estado, datos, version_catalogo, ruta_bitacora="", comandos=0):
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        jugador = estado.jugador
        inventario = jugador.inventario
        elementos = []
        cursor = NINGUNO
        for posicion, nodo in enumerate(inventario.lista.recorrer()):
            elementos.append((nodo.dato.id, inventario.esta_equipado(nodo)))
            if nodo is inventario.actual:
                cursor = posicion
        eventos = [(tiempo, secuencia, evento.tipo, evento.objetivo, evento.dato)
                   for tiempo, secuencia, evento in estado.agenda.pendientes()]
        datos_jugador = DatosJugador(
            jugador.vida, jugador.sala, jugador.proximo_evento.tiempo_siguiente, elementos,
            jugador.velocidad, cursor, estado.acciones, estado.enemigos_derrotados,
            estado.puerta_salida_abierta, estado.antorcha_hasta,
            estado.agenda.siguiente_secuencia(), estado.azar.getstate(), eventos,
            ruta_bitacora, comandos)
        cabecera = DatosCabecera(datos.id, datos.version, version_catalogo, estado.semilla,
                                 estado.tiempo)
        guardar(ruta, cabecera, datos_jugador, GuardadoPartida._salas(estado))

    @staticmethod
    def _salas(estado):
        # las salas con contenido y las salas donde quedó algún enemigo que se movió
        ids = estado.salas_cargadas()
        for enemigo in estado.enemigos_vivos():
            if enemigo.sala not in ids:
                ids.append(enemigo.sala)
        salas = []
        for id_sala in ids:
            sala = estado.esqueleto.obtener(id_sala)
            puertas = [(s.direccion, estado.esqueleto.puerta(id_sala, s.direccion).esta_abierta())
                       for s in sala.salidas]
            enemigos = [(e.instancia, e.tipo, e.vida, e.proximo_evento.tiempo_siguiente
                         if e.proximo_evento is not None else NINGUNO, e.activo)
                        for e in estado.enemigos_vivos() if e.sala == id_sala]
            trampas = [(t.instancia, t.tipo, t.armada) for t in estado.trampas_en(id_sala)]
            rastro = estado.rastro.tiempo_en(id_sala)
            salas.append(DatosSala(id_sala, NINGUNO if rastro is None else rastro, puertas,
                                   estado.suelo(id_sala), enemigos, trampas,
                                   estado.contenido_cargado(id_sala)))
        return salas

    @staticmethod
    def cargar(ruta, datos, version_catalogo, esqueleto, obtener_ficha):
        """Devuelve (EstadoPartida, ruta de la bitácora, comandos que tenía al guardar)."""
        with ArchivoGuardado(ruta) as archivo:
            cabecera = archivo.cabecera
            if (cabecera.cripta_id, cabecera.cripta_version, cabecera.catalogo_version) != \
                    (datos.id, datos.version, version_catalogo):
                raise GuardadoIncompatible(
                    f"el guardado es de {cabecera.cripta_id} v{cabecera.cripta_version} con "
                    f"catálogo {cabecera.catalogo_version}; ahora hay {datos.id} v{datos.version} "
                    f"con catálogo {version_catalogo}")
            guardado = archivo.leer_jugador()
            salas = archivo.leer_todas()

        # las puertas vuelven a como las declaró el API y luego se aplica lo guardado
        esqueleto.reiniciar_puertas()
        jugador = Jugador(guardado.sala, datos.jugador, Inventario(datos.inventario_max))
        jugador.vida = guardado.vida
        jugador.velocidad = guardado.velocidad
        GuardadoPartida._armar_inventario(jugador.inventario, guardado, obtener_ficha)

        estado = EstadoPartida(cabecera.semilla, jugador, esqueleto, obtener_ficha=obtener_ficha)
        estado.configurar_salida(datos.sala_salida, datos.llave_salida)
        estado.controlar_contenido = True
        estado.tiempo = cabecera.reloj
        estado.acciones = guardado.acciones
        estado.enemigos_derrotados = guardado.enemigos_derrotados
        estado.puerta_salida_abierta = guardado.salida_abierta
        estado.antorcha_hasta = guardado.antorcha_hasta
        estado.azar.setstate(guardado.azar)

        for sala in salas:
            estado.restaurar_sala(sala.id, sala.objetos,
                                  [Trampa(inst, tipo, sala.id, armada)
                                   for inst, tipo, armada in sala.trampas],
                                  sala.cargada)
            if sala.rastro != NINGUNO:
                estado.rastro.marcar(sala.id, sala.rastro)
            for direccion, abierta in sala.puertas:
                puerta = esqueleto.puerta(sala.id, direccion)
                if abierta:
                    puerta.abrir()
                else:
                    puerta.cerrar()
            for instancia, tipo, vida, _, activo in sala.enemigos:
                enemigo = estado.colocar_enemigo(InstanciaEnemigo(instancia, tipo, vida),
                                                 obtener_ficha(tipo), sala.id)
                enemigo.activo = activo

        for tiempo, secuencia, tipo, objetivo, dato in guardado.eventos:
            evento = Evento(tipo, objetivo, dato)
            estado.agenda.restaurar(tiempo, secuencia, evento, guardado.siguiente_secuencia)
            if tipo == "accion":
                actor = jugador if objetivo == jugador.id else estado.enemigo(objetivo)
                actor.proximo_evento = evento
        return estado, guardado.bitacora, guardado.comandos

    @staticmethod
    def _armar_inventario(inventario, guardado, obtener_ficha):
        for id_objeto, _ in guardado.inventario:
            inventario.recoger(obtener_ficha(id_objeto))
        for posicion, nodo in enumerate(inventario.lista.recorrer()):
            if guardado.inventario[posicion][1]:
                inventario.marcar_equipado(nodo)
            if posicion == guardado.cursor:
                inventario.actual = nodo