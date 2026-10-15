from vista.estilo import Estilo

ANCHO = 72
DIRECCIONES = (("N", "Norte"), ("S", "Sur"), ("E", "Este"), ("O", "Oeste"))

# lo que el jugador puede escribir y el comando que entiende el controlador
ALIAS = (
    ("norte", "n"), ("sur", "s"), ("este", "e"), ("oeste", "o"),
    ("i", "inv"), ("inventario", "inv"),
    ("z", "esperar"),
    ("?", "ayuda"), ("h", "ayuda"), ("help", "ayuda"),
    ("q", "salir"), ("quit", "salir"), ("exit", "salir"),
)
PALABRAS_DIRECCION = (("norte", "n"), ("sur", "s"), ("este", "e"), ("oeste", "o"),
                      ("n", "n"), ("s", "s"), ("e", "e"), ("o", "o"))
PREFIJOS_DE_ID = ("itm", "ent", "trp")

# qué se puede hacer con cada clase de objeto, para la pista al verlo
USOS = (
    ("arma", "equipar"), ("armadura", "equipar"),
    ("pocion", "usar"), ("antidoto", "usar"), ("antorcha", "usar"),
    ("pergamino_retroceso", "deshacer"), ("llave", "abre puertas, no se gasta"),
)

AYUDA = """
Moverse
  n, s, e, o  (o norte, sur, este, oeste)   ir a la sala vecina ............ 100
  abrir <dir>   ej.: abrir e, abrir este     abrir una puerta con su llave .. 50

Pelear y esperar
  atacar <número o instancia>  ej.: atacar 1  atacar a un enemigo .......... 100
  esperar  (o z)                              dejar pasar el turno .......... 100

Objetos
  recoger [número o id]  ej.: recoger 2       tomar algo del suelo ........... 25
  sig / ant                                   ver el objeto siguiente/anterior
  usar                                        poción, antídoto o antorcha .... 50
  equipar                                     arma o armadura ................ 50
  soltar                                      dejar en el suelo el que ves ... 25
  inv [peso|valor|nombre]  (o i)              ver el inventario, ordenado
  deshacer                                    usar un pergamino de retroceso

Partida
  guardar [nombre] / cargar [nombre]          guardar o cargar (partidas/<nombre>.sav)
  ayuda  (o ?)                                ver esta lista
  salir  (o q)                                terminar la sesión

Los números de "atacar" y "recoger" son los que aparecen en la pantalla de la sala.
Lo que está entre puntos es el tiempo que cuesta la acción.
"""


class Consola:
    """Vista de consola. Solo presenta el estado y recoge comandos: no cambia el modelo.

    Para que sea cómoda de usar recuerda lo último que mostró: así no repite la sala si
    nada cambió, marca los mensajes nuevos y entiende 'atacar 1' o 'recoger 2'
    según las listas de la última pantalla."""

    def __init__(self):
        self._estilo = Estilo()
        self._estado = None
        self._huella = None          # lo que había en la última pantalla dibujada
        self._nuevos = []            # mensajes del último comando que aún no se mostraron
        self._enemigos_vistos = []   # instancias, en el orden numerado de la pantalla
        self._suelo_visto = []       # ids del suelo, en el mismo orden

    # ------------------------------------------------------------ entrada

    def elegir_cripta(self, criptas):
        """Muestra las criptas disponibles y devuelve el id elegido (None si no hay o se cancela)."""
        if not criptas:
            print("No hay criptas disponibles.")
            return None
        print()
        print(self._titulo("CRIPTA  -  elige dónde entrar"))
        print(f"  {'#':>2}  {'Nombre':<26} {'Id':<12} {'Salas':>6}  Dificultad")
        for numero, cripta in enumerate(criptas, 1):
            print(f"  {numero:>2}  {cripta.nombre:<26} {cripta.id:<12} {cripta.salas:>6}  "
                  f"{'*' * cripta.dificultad}")
        while True:
            try:
                texto = input("Elige una cripta (número o id): ").strip()
            except EOFError:
                return None
            for numero, cripta in enumerate(criptas, 1):
                if texto in (str(numero), cripta.id):
                    return cripta.id
            print(self._color("Esa cripta no está en la lista.", "alerta"))

    def pedir_comando(self):
        estado = self._estado
        contexto = ""
        if estado is not None:
            jugador = estado.jugador
            contexto = f"[t={estado.tiempo} | vida {jugador.vida}/{jugador.vida_max}] "
        try:
            texto = input(self._color(contexto, "tenue") + "> ")
        except EOFError:
            return None
        return self._traducir(texto)

    def pedir_nombre(self):
        try:
            return input("Tu nombre para la tabla de puntajes: ")
        except EOFError:
            return ""

    def _traducir(self, texto):
        """Convierte lo que escribió el jugador al comando que entiende el controlador.
        La bitácora de la partida guarda el comando ya traducido, así el replay no depende
        de esta pantalla."""
        partes = texto.strip().split()
        if not partes:
            return texto
        orden = partes[0].lower()
        if len(partes) == 1:
            for alias, comando in ALIAS:
                if orden == alias:
                    return comando
            return texto.strip()
        argumento = partes[1].lower()
        if orden in ("abrir", "mover", "ir"):
            for palabra, letra in PALABRAS_DIRECCION:
                if argumento == palabra:
                    return f"abrir {letra}" if orden == "abrir" else letra
        if argumento.isdigit():
            numero = int(argumento)
            if orden == "atacar" and 1 <= numero <= len(self._enemigos_vistos):
                return f"atacar {self._enemigos_vistos[numero - 1]}"
            if orden == "recoger" and 1 <= numero <= len(self._suelo_visto):
                return f"recoger {self._suelo_visto[numero - 1]}"
        return texto.strip()

    # ------------------------------------------------------------ partida

    def mostrar_partida(self, estado, esqueleto, mensajes):
        self._estado = estado
        jugador = estado.jugador
        huella = (id(estado), estado.tiempo, jugador.sala, estado.acciones,
                  len(jugador.inventario), jugador.vida)
        if huella == self._huella:
            # nada cambió (consultas, comandos rechazados): no se repite la pantalla
            self._mostrar_nuevos()
            return
        self._huella = huella
        sala = esqueleto.obtener(jugador.sala)
        print()
        print(self._titulo(f"Sala {sala.id}  -  {sala.nombre}", f"tiempo {estado.tiempo}"))
        self._mostrar_salidas(estado, esqueleto, sala)
        self._mostrar_enemigos(estado, sala.id)
        self._mostrar_suelo(estado, sala.id)
        print(self._color("-" * ANCHO, "tenue"))
        self._mostrar_jugador(estado)
        print(self._color("-" * ANCHO, "tenue"))
        self.mostrar_bitacora(mensajes)

    def _mostrar_salidas(self, estado, esqueleto, sala):
        print(self._color(" Salidas", "negrita"))
        if not sala.salidas:
            print("   ninguna")
        for salida in sala.salidas:
            destino = esqueleto.obtener(salida.sala_destino)
            nombre = destino.nombre if destino is not None else "sala desconocida"
            linea = f"   {self._direccion(salida.direccion):<6} -> {nombre} ({salida.sala_destino})"
            puerta = esqueleto.puerta(sala.id, salida.direccion)
            if puerta.esta_cerrada():
                if estado.jugador.puede_abrir(puerta):
                    nota = self._color(f"[cerrada: tienes la llave, escribe 'abrir "
                                       f"{salida.direccion.lower()}']", "ok")
                else:
                    nota = self._color(f"[cerrada: falta {self._legible(puerta.llave)}]",
                                       "alerta")
                linea += "   " + nota
            print(linea)

    def _mostrar_enemigos(self, estado, id_sala):
        enemigos = estado.enemigos_en_sala(id_sala)
        self._enemigos_vistos = [e.instancia for e in enemigos]
        if not enemigos:
            print(self._color(" Enemigos", "negrita") + "   ninguno")
            return
        print(self._color(" Enemigos", "negrita") + self._color("   (atacar <número>)", "tenue"))
        for numero, enemigo in enumerate(enemigos, 1):
            print(f"   {numero}. {enemigo.nombre} {enemigo.instancia:<10} "
                  f"{self._barra(enemigo.vida, enemigo.vida_max)} "
                  f"{enemigo.vida}/{enemigo.vida_max}  {enemigo.comportamiento or ''}")

    def _mostrar_suelo(self, estado, id_sala):
        suelo = estado.suelo(id_sala)
        self._suelo_visto = list(suelo)
        if not suelo:
            print(self._color(" En el suelo", "negrita") + "   nada")
        else:
            print(self._color(" En el suelo", "negrita") + self._color("   (recoger <número>)",
                                                                       "tenue"))
            for numero, id_objeto in enumerate(suelo, 1):
                print(f"   {numero}. {self._legible(id_objeto):<24} "
                      + self._color(f"({id_objeto})", "tenue"))
        trampas = estado.trampas_en(id_sala)
        if trampas:
            detalle = ", ".join(f"{self._legible(t.tipo)} ({'armada' if t.armada else 'desarmada'})"
                                for t in trampas)
            print(self._color(" Trampas", "negrita") + "   " + self._color(detalle, "peligro"))

    def _mostrar_jugador(self, estado):
        jugador = estado.jugador
        inventario = jugador.inventario
        estilo_vida = "peligro" if jugador.vida * 3 <= jugador.vida_max else "ok"
        print(self._color(" Tú", "negrita") + "   vida "
              + self._color(self._barra(jugador.vida, jugador.vida_max, 20), estilo_vida)
              + f" {jugador.vida}/{jugador.vida_max}   ataque {jugador.ataque_efectivo()}"
              f"   defensa {jugador.defensa_efectiva()}   velocidad {jugador.velocidad}")
        arma = inventario.arma_equipada()
        armadura = inventario.armadura_equipada()
        print(f"      arma: {arma.nombre if arma else '-'}"
              f"   armadura: {armadura.nombre if armadura else '-'}")
        efectos = []
        if estado.antorcha_hasta is not None:
            efectos.append(f"antorcha encendida hasta t={estado.antorcha_hasta}")
        if estado.veneno_hasta is not None:
            efectos.append(self._color(f"envenenado ({estado.veneno_dano} cada 80) hasta "
                                       f"t={estado.veneno_hasta}", "peligro"))
        if efectos:
            print("      efectos: " + ", ".join(efectos))
        actual = inventario.obtener_actual()
        print(f"      inventario {len(inventario)}/{inventario.capacidad}"
              + (f"   viendo: {actual.nombre}" if actual is not None else "")
              + f"   pergaminos: {inventario.cantidad_pergaminos()}")

    def mostrar_resultado(self, comando, mensajes):
        # se muestran en la siguiente pantalla (o al final), así no salen dos veces
        self._nuevos = list(mensajes)

    def _mostrar_nuevos(self):
        for mensaje in self._nuevos:
            print(self._color("» " + mensaje, "nuevo"))
        self._nuevos = []

    def mostrar_bitacora(self, mensajes):
        cantidad = "1 mensaje" if len(mensajes) == 1 else f"{len(mensajes)} mensajes"
        print(self._color(" Bitácora", "negrita") + self._color(f"   (últimos 20; ahora {cantidad})",
                                                                "tenue"))
        primero_nuevo = len(mensajes) - len(self._nuevos)
        for i, mensaje in enumerate(mensajes):
            if i >= primero_nuevo:
                print(self._color("  » " + mensaje, "nuevo"))
            else:
                print(self._color("    " + mensaje, "tenue"))
        self._nuevos = []

    # ------------------------------------------------------------ inventario

    def mostrar_objeto_actual(self, objeto):
        if objeto is None:
            print("El inventario está vacío.")
            return
        print(f"Ahora ves: {self._color(objeto.nombre, 'negrita')} ({objeto.clase}, "
              f"peso {objeto.peso}, valor {objeto.valor})"
              + self._color(f"  -> {self._uso(objeto.clase)}", "tenue"))

    def mostrar_inventario_detallado(self, pares):
        print(self._color(" Inventario", "negrita"))
        if not pares:
            print("   (vacío)")
            return
        print(self._color(f"   {'#':>2}  {'Objeto':<30} {'Clase':<20} {'Peso':>4} {'Valor':>6}",
                          "tenue"))
        for numero, (objeto, equipado) in enumerate(pares, 1):
            marca = " [equipado]" if equipado else ""
            print(f"   {numero:>2}  {objeto.nombre + marca:<30} {objeto.clase:<20} "
                  f"{objeto.peso:>4} {objeto.valor:>6}")

    def mostrar_ayuda(self):
        print(self._titulo("Comandos"))
        print(AYUDA)

    # ------------------------------------------------------------ final

    def mostrar_fin(self, estado):
        self._mostrar_nuevos()
        print()
        if estado.resultado == "victoria":
            print(self._titulo("¡VICTORIA!  Saliste de la cripta"))
        elif estado.resultado == "derrota":
            print(self._color("=" * ANCHO, "peligro"))
            print(self._color("  DERROTA  -  caíste en la cripta", "peligro"))
            print(self._color("=" * ANCHO, "peligro"))
        else:
            print(self._titulo("Partida sin terminar"))
        print(f"  Acciones: {estado.acciones}   Enemigos derrotados: {estado.enemigos_derrotados}"
              f"   Tiempo final: {estado.tiempo}")

    def mostrar_puntajes(self, registros):
        print()
        print(self._titulo("Tabla de puntajes"))
        print(self._color(f"  {'#':>2}  {'Nombre':<15} {'Cripta':<11} {'Resultado':<10} "
                          f"{'Acciones':>8} {'Enemigos':>8} {'Tiempo':>7}", "tenue"))
        for posicion, registro in enumerate(registros[:10], 1):
            print(f"  {posicion:>2}  {registro.nombre[:15]:<15} {registro.cripta_id[:11]:<11} "
                  f"{registro.resultado:<10} {registro.acciones:>8} "
                  f"{registro.enemigos_derrotados:>8} {registro.tiempo_final:>7}")

    def mostrar_reporte(self, solicitudes, presupuesto, aciertos, fallos):
        print()
        print(f"  Solicitudes de red: {solicitudes} de {presupuesto}"
              f"   |   Caché del catálogo: {aciertos} aciertos, {fallos} fallos")

    # ------------------------------------------------------------ formato

    def _titulo(self, texto, derecha=""):
        relleno = max(1, ANCHO - len(texto) - len(derecha) - 2)
        linea = "=" * ANCHO
        return "\n".join((self._color(linea, "titulo"),
                          self._color(f" {texto}{' ' * relleno}{derecha} ", "titulo"),
                          self._color(linea, "titulo")))

    def _color(self, texto, estilo):
        return self._estilo.aplicar(texto, estilo)

    @staticmethod
    def _barra(actual, maximo, ancho=10):
        llenos = 0 if maximo <= 0 else round(ancho * max(0, actual) / maximo)
        llenos = min(ancho, llenos)
        return "[" + "#" * llenos + "-" * (ancho - llenos) + "]"

    @staticmethod
    def _direccion(letra):
        for corta, larga in DIRECCIONES:
            if corta == letra:
                return larga
        return letra

    @staticmethod
    def _legible(id_catalogo):
        """'itm_daga_oxidada' -> 'daga oxidada'. La vista no consulta el catálogo."""
        if id_catalogo is None:
            return "-"
        partes = str(id_catalogo).split("_")
        if len(partes) > 1 and partes[0] in PREFIJOS_DE_ID:
            partes = partes[1:]
        return " ".join(partes)

    @staticmethod
    def _uso(clase):
        for nombre, uso in USOS:
            if nombre == clase:
                return uso
        return "soltar"
