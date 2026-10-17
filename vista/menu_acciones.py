DIRECCIONES = (("N", "Norte"), ("S", "Sur"), ("E", "Este"), ("O", "Oeste"))
PREFIJOS_DE_ID = ("itm", "ent", "trp")
CLASES_USABLES = ("pocion", "antidoto", "antorcha")
CLASES_EQUIPABLES = ("arma", "armadura")

# tipo de cada acción, para que la vista le dé un color
MOVER = "mover"
ABRIR = "abrir"
ATACAR = "atacar"
RECOGER = "recoger"
OBJETO = "objeto"
OTRA = "otra"


class MenuAcciones:
    """Arma la lista de lo que el jugador puede hacer ahora mismo. Cada opción trae su
    texto, su tipo y los comandos que la realizan (por ejemplo 'sig', 'sig', 'usar'
    para usar el tercer objeto del inventario). Solo lee el estado: no cambia nada."""

    def armar(self, estado, esqueleto):
        jugador = estado.jugador
        sala = esqueleto.obtener(jugador.sala)
        if sala is None or estado.terminada():
            return []
        opciones = []
        self._salidas(opciones, estado, esqueleto, sala)
        self._enemigos(opciones, estado, sala.id)
        self._suelo(opciones, estado, sala.id)
        self._inventario(opciones, estado)
        opciones.append(("Esperar (dejar pasar el turno)", OTRA, ("esperar",)))
        inventario = jugador.inventario
        if inventario.cantidad_pergaminos() > 0 and estado.historial.acciones_guardadas() > 0:
            opciones.append(("Leer un pergamino: deshacer la última acción", OTRA, ("deshacer",)))
        actual = inventario.obtener_actual()
        if inventario.esta_lleno() and actual is not None:
            # con el inventario lleno hace falta poder soltar algo para recoger
            opciones.append((f"Soltar {actual.nombre} (el que estás viendo)", OTRA, ("soltar",)))
        return opciones

    def _salidas(self, opciones, estado, esqueleto, sala):
        for salida in sala.salidas:
            destino = esqueleto.obtener(salida.sala_destino)
            nombre = destino.nombre if destino is not None else f"sala {salida.sala_destino}"
            direccion = self.nombre_direccion(salida.direccion)
            letra = salida.direccion.lower()
            puerta = esqueleto.puerta(sala.id, salida.direccion)
            if puerta is None or puerta.esta_abierta():
                opciones.append((f"Ir al {direccion:<5} -> {nombre}", MOVER, (letra,)))
            elif estado.jugador.puede_abrir(puerta):
                opciones.append((f"Abrir la puerta del {direccion} (tienes la llave)", ABRIR,
                                 (f"abrir {letra}",)))

    @staticmethod
    def _enemigos(opciones, estado, id_sala):
        for enemigo in estado.enemigos_en_sala(id_sala):
            opciones.append((f"Atacar a {enemigo.nombre} {enemigo.instancia} "
                             f"({enemigo.vida}/{enemigo.vida_max} de vida)", ATACAR,
                             (f"atacar {enemigo.instancia}",)))

    def _suelo(self, opciones, estado, id_sala):
        if estado.jugador.inventario.esta_lleno():
            return
        ya_ofrecidos = []
        for id_objeto in estado.suelo(id_sala):
            if id_objeto in ya_ofrecidos:
                continue
            ya_ofrecidos.append(id_objeto)
            opciones.append((f"Recoger {self.legible(id_objeto)}", RECOGER,
                             (f"recoger {id_objeto}",)))

    def _inventario(self, opciones, estado):
        inventario = estado.jugador.inventario
        nodos = list(inventario.lista.recorrer())
        posicion_actual = 0
        for posicion, nodo in enumerate(nodos):
            if nodo is inventario.actual:
                posicion_actual = posicion
        ya_ofrecidos = []
        for posicion, nodo in enumerate(nodos):
            objeto = nodo.dato
            if objeto.clase in CLASES_USABLES:
                verbo = "usar"
            elif objeto.clase in CLASES_EQUIPABLES and not inventario.esta_equipado(nodo):
                verbo = "equipar"
            else:
                continue
            if (verbo, objeto.id) in ya_ofrecidos:
                continue
            ya_ofrecidos.append((verbo, objeto.id))
            # usar y equipar actúan sobre el objeto que se está viendo: primero se mueve el
            # cursor hasta él (el inventario no da la vuelta, por eso se cuenta en qué sentido)
            if posicion >= posicion_actual:
                pasos = ("sig",) * (posicion - posicion_actual)
            else:
                pasos = ("ant",) * (posicion_actual - posicion)
            opciones.append((f"{verbo.capitalize()} {objeto.nombre}{self._detalle(objeto, estado)}",
                             OBJETO, pasos + (verbo,)))

    @staticmethod
    def _detalle(objeto, estado):
        if objeto.clase == "arma":
            return f" (+{objeto.ataque_bonus or 0} de ataque)"
        if objeto.clase == "armadura":
            return f" (+{objeto.defensa_bonus or 0} de defensa)"
        if objeto.clase == "antorcha":
            return f" (luz durante {objeto.duracion or 0})"
        if objeto.clase == "antidoto":
            return " (cura el veneno)" if estado.veneno_hasta is not None \
                else " (ahora no estás envenenado)"
        partes = []
        if objeto.cura:
            partes.append(f"cura {objeto.cura}")
        if objeto.modificador_velocidad and objeto.duracion:
            partes.append(f"velocidad {objeto.modificador_velocidad:+} durante {objeto.duracion}")
        return f" ({', '.join(partes)})" if partes else ""

    @staticmethod
    def nombre_direccion(letra):
        for corta, larga in DIRECCIONES:
            if corta == letra:
                return larga
        return letra

    @staticmethod
    def legible(id_catalogo):
        """'itm_daga_oxidada' -> 'daga oxidada'. La vista no consulta el catálogo."""
        if id_catalogo is None:
            return "-"
        partes = str(id_catalogo).split("_")
        if len(partes) > 1 and partes[0] in PREFIJOS_DE_ID:
            partes = partes[1:]
        return " ".join(partes)
