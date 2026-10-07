import os
from datetime import datetime

from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.error_fuente_datos import ErrorFuenteDatos
from adaptadores.guardado_binario import GuardadoIncompatible, GuardadoInvalido
from adaptadores.guardado_partida import GuardadoPartida
from estructuras.vector_ordenado import VectorOrdenado
from modelo.bitacora import Bitacora
from modelo.esqueleto import Esqueleto
from modelo.estado_partida import DERROTA, VICTORIA, EstadoPartida
from modelo.inventario import Inventario
from modelo.jugador import Jugador
from modelo.movimiento import MovimientoInvalido
from modelo.precarga import salas_a_precargar
from modelo.registro_puntaje import RegistroPuntaje

DIRECCIONES = ("N", "S", "E", "O")
CRITERIOS_INVENTARIO = ("peso", "valor", "nombre")
# guardar y cargar no van a la bitácora: el replay no debe tocar archivos
SIN_BITACORA = ("guardar", "cargar", "ayuda", "inv")


class ControladorPartida:
    """Traduce los comandos del jugador a operaciones del modelo, trae el contenido
    de las salas antes de que haga falta y avisa a la vista. No dibuja nada."""

    def __init__(self, datos, fuente, cache, vista, semilla, version_catalogo="",
                 carpeta_partidas="partidas"):
        self.datos = datos
        self.version_catalogo = version_catalogo
        self.carpeta_partidas = carpeta_partidas
        self._bitacora_partida = None
        self._comandos = 0
        self.fuente = fuente
        self.cache = cache
        self.vista = vista
        self.bitacora = Bitacora()
        self.estado = None
        self._pedidas = VectorOrdenado()   # salas cuyo contenido ya se pidió
        self._nuevos = []
        self.esqueleto = self._cargar_esqueleto()
        jugador = Jugador(datos.sala_inicial, datos.jugador, Inventario(datos.inventario_max))
        self.estado = EstadoPartida(semilla, jugador, self.esqueleto, obtener_ficha=cache.obtener)
        self.estado.configurar_salida(datos.sala_salida, datos.llave_salida)
        self.estado.controlar_contenido = True
        # la sala inicial tiene que estar cargada antes de la primera acción
        self._precargar(datos.sala_inicial)
        if not self.estado.contenido_cargado(datos.sala_inicial):
            raise ErrorFuenteDatos("no se pudo cargar el contenido de la sala inicial")
        self.estado.iniciar()
        self._avisar(f"Entras a {self.esqueleto.obtener(datos.sala_inicial).nombre}.")

    # ----------------------------------------------------------------- bucle

    def jugar(self, leer_comando, bitacora_partida=None):
        """leer_comando() devuelve el siguiente comando o None si no hay más."""
        self._bitacora_partida = bitacora_partida
        while not self.estado.terminada():
            self.vista.mostrar_partida(self.estado, self.esqueleto, self.bitacora.ultimos())
            comando = leer_comando()
            if comando is None:
                break
            comando = comando.strip()
            if not comando:
                continue
            if comando.lower() == "salir":
                break
            if self._bitacora_partida is not None and                     comando.split()[0].lower() not in SIN_BITACORA:
                self._bitacora_partida.anotar(comando)
                self._comandos += 1
            self.ejecutar(comando)
        self.vista.mostrar_fin(self.estado)

    def ejecutar(self, texto):
        self._nuevos = []
        partes = texto.split()
        orden = partes[0].lower()
        argumento = partes[1] if len(partes) > 1 else None
        try:
            if orden.upper() in DIRECCIONES or orden == "mover":
                direccion = orden.upper() if orden != "mover" else (argumento or "").upper()
                self._mover(direccion)
            elif orden == "abrir":
                self.estado.abrir_puerta((argumento or "").upper())
                self._avisar("Abres la puerta.")
                self._despues_de_actuar()
            elif orden == "atacar":
                self._avisar_golpe(self.estado.jugador_ataca(argumento))
                self._despues_de_actuar()
            elif orden == "esperar":
                self.estado.esperar()
                self._despues_de_actuar()
            elif orden == "recoger":
                ficha = self.estado.recoger(argumento)
                self._avisar(f"Recoges {ficha.nombre}.")
                self._despues_de_actuar()
            elif orden == "soltar":
                self._avisar(f"Sueltas {self.estado.soltar().nombre}.")
                self._despues_de_actuar()
            elif orden == "equipar":
                self._avisar(f"Equipas {self.estado.equipar().nombre}.")
                self._despues_de_actuar()
            elif orden == "usar":
                self._avisar(f"Usas {self.estado.usar().nombre}.")
                self._despues_de_actuar()
            elif orden == "deshacer":
                self.estado.deshacer()
                self._avisar("Lees el pergamino: el tiempo retrocede una acción.")
            elif orden in ("sig", "ant"):
                inventario = self.estado.jugador.inventario
                if orden == "sig":
                    inventario.avanzar()
                else:
                    inventario.retroceder()
                self.vista.mostrar_objeto_actual(inventario.obtener_actual())
            elif orden == "inv":
                criterio = argumento.lower() if argumento else None
                if criterio is not None and criterio not in CRITERIOS_INVENTARIO:
                    raise MovimientoInvalido("criterio", "ordena por peso, valor o nombre")
                self.vista.mostrar_inventario_detallado(
                    self.estado.jugador.inventario.vista_detallada(criterio))
            elif orden == "guardar":
                self._guardar(argumento or "guardado")
            elif orden == "cargar":
                self._cargar(argumento or "guardado")
            elif orden == "ayuda":
                self.vista.mostrar_ayuda()
            else:
                self._avisar(f"No entiendo '{texto}'. Escribe ayuda para ver los comandos.")
        except MovimientoInvalido as error:
            self._avisar(f"No se puede: {error}.")
        self.vista.mostrar_resultado(texto, self._nuevos)

    # ---------------------------------------------------------------- acciones

    def _mover(self, direccion):
        salida = self.esqueleto.salida(self.estado.jugador.sala, direccion)
        if salida is not None and not self.estado.contenido_cargado(salida.sala_destino):
            # se trae antes de confirmar el movimiento; esperar la red no mueve el reloj
            self._precargar(salida.sala_destino)
        destino = self.estado.mover_jugador(direccion)
        self._avisar(f"Entras a {self.esqueleto.obtener(destino).nombre}.")
        if self.estado.resultado == VICTORIA:
            self._avisar("¡Llegaste a la salida! Ganaste.")
            return
        self._despues_de_actuar()

    def _despues_de_actuar(self):
        if self.estado.terminada():
            return
        for golpe in self.estado.avanzar_hasta_turno_jugador():
            self._avisar_golpe(golpe)
        if self.estado.resultado == DERROTA:
            self._avisar("Caíste en la cripta. Fin de la partida.")
            return
        self._precargar_vecinas()

    def _avisar_golpe(self, golpe):
        if golpe.atacante is self.estado.jugador:
            texto = f"Golpeas a {self._nombre(golpe.defensor)} por {golpe.dano}."
            if golpe.murio:
                texto += " Cae muerto."
        else:
            texto = f"{self._nombre(golpe.atacante)} te golpea por {golpe.dano}."
        self._avisar(texto)

    @staticmethod
    def _nombre(enemigo):
        return f"{enemigo.nombre} {enemigo.instancia}"

    def _avisar(self, texto):
        self.bitacora.agregar(texto)
        self._nuevos.append(texto)

    # --------------------------------------------------------- guardar y cargar

    def _ruta_guardado(self, nombre):
        return os.path.join(self.carpeta_partidas, f"{nombre}.sav")

    def _guardar(self, nombre):
        if self.estado.terminada():
            raise MovimientoInvalido("guardar", "la partida ya terminó")
        ruta = self._ruta_guardado(nombre)
        ruta_bitacora = "" if self._bitacora_partida is None else self._bitacora_partida.ruta
        GuardadoPartida.guardar(ruta, self.estado, self.datos, self.version_catalogo,
                                ruta_bitacora, self._comandos)
        self._avisar(f"Partida guardada en {ruta}.")

    def _cargar(self, nombre):
        ruta = self._ruta_guardado(nombre)
        try:
            estado, ruta_bitacora, comandos = GuardadoPartida.cargar(
                ruta, self.datos, self.version_catalogo, self.esqueleto, self.cache.obtener)
        except FileNotFoundError:
            raise MovimientoInvalido("cargar", f"no existe el guardado {ruta}")
        except (GuardadoInvalido, GuardadoIncompatible, ErrorFuenteDatos) as error:
            raise MovimientoInvalido("cargar", f"no se puede cargar {ruta}: {error}")
        self.estado = estado
        self._pedidas = VectorOrdenado()
        for sala in estado.salas_cargadas():
            self._pedidas.insertar(sala, True)
        if self._bitacora_partida is not None:
            # bitácora nueva: lo jugado hasta el guardado y desde aquí lo que siga
            nueva = os.path.join(self.carpeta_partidas,
                                 f"partida-{datetime.now():%Y%m%d-%H%M%S}-cargada.log")
            cabecera = CabeceraPartida(self.datos.id, self.datos.version, self.version_catalogo,
                                       estado.semilla)
            self._bitacora_partida = BitacoraPartida.continuar(nueva, cabecera, ruta_bitacora,
                                                               comandos)
            self._comandos = comandos
        self._avisar(f"Partida cargada desde {ruta}.")

    # ------------------------------------------------------------- contenido

    def _cargar_esqueleto(self):
        esqueleto = Esqueleto()
        for numero in range(1, self.datos.paginas + 1):
            esqueleto.agregar_pagina(self.fuente.pagina_salas(self.datos.id, numero))
        return esqueleto

    def _precargar_vecinas(self):
        sala = self.esqueleto.obtener(self.estado.jugador.sala)
        for salida in sala.salidas:
            if not self._pedidas.contiene(salida.sala_destino):
                self._precargar(self.estado.jugador.sala)
                return

    def _precargar(self, desde):
        """Pide en un solo lote las salas más cercanas que aún no se pidieron."""
        lote = salas_a_precargar(self.esqueleto, desde, self._pedidas.contiene)
        if not lote:
            return
        try:
            contenidos = self.fuente.contenido(self.datos.id, lote)
            tipos = []
            for contenido in contenidos:
                tipos.extend(e.tipo for e in contenido.enemigos)
                tipos.extend(contenido.objetos)
                tipos.extend(t.tipo for t in contenido.trampas)
            fichas = self.cache.resolver(tipos) if tipos else []
            # lo que sueltan los enemigos también tiene que estar disponible
            soltados = []
            for ficha in fichas:
                soltados.extend(ficha.suelta)
            if soltados:
                self.cache.resolver(soltados)
        except (ErrorFuenteDatos, KeyError) as error:
            self._avisar(f"No se pudo traer el contenido de las salas {lote}: {error}")
            return
        for sala in lote:
            self._pedidas.insertar(sala, True)
        for contenido in contenidos:
            self.estado.cargar_contenido(contenido)

    # ------------------------------------------------------------------ cierre

    def registro_puntaje(self, nombre):
        estado = self.estado
        return RegistroPuntaje(nombre, self.datos.id, self.datos.version, estado.resultado,
                               estado.acciones, estado.enemigos_derrotados, estado.tiempo)
