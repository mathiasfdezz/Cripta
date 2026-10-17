from vista.estilo import Estilo
from vista.menu_acciones import ABRIR, ATACAR, MOVER, OBJETO, RECOGER, MenuAcciones

ANCHO = 72

# lo que el jugador puede escribir y el comando que entiende el controlador
ALIAS = (
    ("norte", "n"), ("sur", "s"), ("este", "e"), ("oeste", "o"),
    ("i", "inv"), ("inventario", "inv"),
    ("z", "esperar"),
    ("g", "guardar"), ("c", "cargar"),
    ("?", "ayuda"), ("h", "ayuda"), ("help", "ayuda"),
    ("q", "salir"), ("quit", "salir"), ("exit", "salir"),
)
PALABRAS_DIRECCION = (("norte", "n"), ("sur", "s"), ("este", "e"), ("oeste", "o"),
                      ("n", "n"), ("s", "s"), ("e", "e"), ("o", "o"))

# color de cada tipo de opción del menú
COLOR_DE_OPCION = ((MOVER, "ok"), (ABRIR, "ok"), (ATACAR, "peligro"), (RECOGER, "alerta"),
                   (OBJETO, "titulo"))

# qué se puede hacer con cada clase de objeto, para la pista al verlo
USOS = (
    ("arma", "equipar"), ("armadura", "equipar"),
    ("pocion", "usar"), ("antidoto", "usar"), ("antorcha", "usar"),
    ("pergamino_retroceso", "deshacer"), ("llave", "abre puertas, no se gasta"),
)

# si el juego responde con esto, el comando no se hizo
INICIOS_DE_RECHAZO = ("No se puede", "No entiendo")

AYUDA = """
La forma más fácil: escribe el NÚMERO de una opción del menú "¿Qué haces?".
El menú solo muestra lo que se puede hacer ahora mismo.

Atajos que funcionan siempre
  i  inventario completo        g  guardar la partida      c  cargar la partida
  ?  esta ayuda                 q  salir

Si prefieres escribir los comandos (entre puntos, el tiempo que cuestan):
  n, s, e, o  (o norte, sur...)       moverse ............................ 100
  abrir <dir>   ej.: abrir este       abrir una puerta con su llave ....... 50
  atacar <n>    ej.: atacar 1         atacar al enemigo número n .......... 100
  esperar  (o z)                      dejar pasar el turno ................ 100
  recoger <n>   ej.: recoger 2        tomar el objeto número n del suelo .. 25
  sig / ant                           ver el objeto siguiente / anterior
  usar / equipar / soltar             sobre el objeto que estás viendo .... 50 / 50 / 25
  inv [peso|valor|nombre]             ver el inventario, ordenado si se indica
  deshacer                            usar un pergamino de retroceso
  guardar [nombre] / cargar [nombre]  partidas/<nombre>.sav
"""


class Consola:
    """Vista de consola. Solo presenta el estado y recoge comandos: no cambia el modelo.

    Para que sea fácil de usar, después de cada pantalla muestra un menú numerado con lo
    que se puede hacer y traduce el número elegido a los comandos del juego. Una opción
    puede necesitar varios comandos (por ejemplo 'sig', 'sig', 'usar'): se entregan uno
    por uno y, si alguno se rechaza, se cancelan los que faltaban. La bitácora de la
    partida guarda siempre los comandos reales, así el replay no depende de esta pantalla."""

    def __init__(self):
        self._estilo = Estilo()
        self._menu = MenuAcciones()
        self._estado = None
        self._huella = None          # lo que había en la última pantalla dibujada
        self._nuevos = []            # mensajes del último comando que aún no se mostraron
        self._opciones = []          # menú de la última pantalla: (texto, tipo, comandos)
        self._pendientes = []        # comandos que faltan de la opción elegida
        self._enemigos_vistos = []   # instancias, en el orden numerado de la pantalla
        self._suelo_visto = []       # ids del suelo, en el mismo orden
        self._sin_entrada = False    # se acabó la entrada (fin de archivo)

    # ------------------------------------------------------------ entrada

    def elegir_cripta(self, criptas):
        """Muestra las criptas disponibles y devuelve el id elegido (None si no hay o se cancela)."""
        if not criptas:
            print("No hay criptas disponibles.")
            return None
        print()
        print(self._titulo("CRIPTA  -  elige dónde entrar"))
        print(self._color(f"  {'#':>2}  {'Nombre':<26} {'Id':<12} {'Salas':>6}  Dificultad",
                          "tenue"))
        for numero, cripta in enumerate(criptas, 1):
            print(f"  {numero:>2}  {cripta.nombre:<26} {cripta.id:<12} {cripta.salas:>6}  "
                  f"{'*' * max(0, cripta.dificultad or 0)}")
        while True:
            texto = self._leer("Elige una cripta (número o id): ")
            if texto is None:
                return None
            texto = texto.strip()
            for numero, cripta in enumerate(criptas, 1):
                if texto in (str(numero), cripta.id):
                    return cripta.id
            print(self._color("Esa cripta no está en la lista.", "alerta"))

    def pedir_comando(self):
        if self._pendientes:
            # sigue la opción elegida antes, sin volver a preguntar
            return self._pendientes.pop(0)
        estado = self._estado
        contexto = ""
        if estado is not None:
            jugador = estado.jugador
            contexto = f"[t={estado.tiempo} | vida {jugador.vida}/{jugador.vida_max}] "
        texto = self._leer(self._color(contexto, "tenue") + "Elige una opción: ")
        if texto is None:
            # sin más entrada (o Ctrl+C): la partida termina ordenadamente
            return None if self._sin_entrada else "salir"
        return self._traducir(texto)

    def pedir_nombre(self):
        texto = self._leer("Tu nombre para la tabla de puntajes: ")
        return "" if texto is None else texto.strip()[:30]

    def _leer(self, pregunta):
        """input() que nunca deja escapar un Ctrl+C ni el fin de la entrada."""
        self._sin_entrada = False
        try:
            return input(pregunta)
        except EOFError:
            self._sin_entrada = True
            return None
        except KeyboardInterrupt:
            print()
            return None

    def _traducir(self, texto):
        """Convierte lo que escribió el jugador en el comando que entiende el controlador."""
        partes = texto.strip().split()
        if not partes:
            return texto
        orden = partes[0].lower()
        if len(partes) == 1:
            if orden.isdigit():
                return self._elegir_opcion(int(orden), texto)
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

    def _elegir_opcion(self, numero, texto):
        if not 1 <= numero <= len(self._opciones):
            print(self._color(f"No hay una opción {numero}. Elige un número del menú.", "alerta"))
            # un comando vacío no llega al juego: se vuelve a mostrar el menú
            return ""
        comandos = list(self._opciones[numero - 1][2])
        self._pendientes = comandos[1:]
        return comandos[0]

    # ------------------------------------------------------------ partida

    def mostrar_partida(self, estado, esqueleto, mensajes):
        self._estado = estado
        self._opciones = self._menu.armar(estado, esqueleto)
        if self._pendientes:
            # en medio de una opción de varios pasos no se dibuja nada
            return
        jugador = estado.jugador
        huella = (id(estado), estado.tiempo, jugador.sala, estado.acciones,
                  len(jugador.inventario), jugador.vida)
        if huella == self._huella:
            # nada cambió (consultas, comandos rechazados): no se repite la sala
            self._mostrar_nuevos()
            self._mostrar_menu()
            return
        self._huella = huella
        sala = esqueleto.obtener(jugador.sala)
        print()
        nombre = sala.nombre if sala.nombre != f"Sala {sala.id}" else ""
        titulo = f"Sala {sala.id}  -  {nombre}" if nombre else f"Sala {sala.id}"
        print(self._titulo(titulo, f"tiempo {estado.tiempo}"))
        self._mostrar_salidas(estado, esqueleto, sala)
        self._mostrar_enemigos(estado, sala.id)
        self._mostrar_suelo(estado, sala.id)
        print(self._color("-" * ANCHO, "tenue"))
        self._mostrar_jugador(estado)
        print(self._color("-" * ANCHO, "tenue"))
        self.mostrar_bitacora(mensajes)
        self._mostrar_menu()

    def _mostrar_menu(self):
        print(self._color(" ¿Qué haces?", "negrita") + self._color("   (escribe el número)", "tenue"))
        for numero, (texto, tipo, _) in enumerate(self._opciones, 1):
            print(f"  {self._color(f'{numero:>2})', self._color_de(tipo))} {texto}")
        print(self._color("  i inventario | g guardar | c cargar | ? ayuda | q salir", "tenue"))

    def _mostrar_salidas(self, estado, esqueleto, sala):
        print(self._color(" Salidas", "negrita"))
        if not sala.salidas:
            print("   ninguna")
        for salida in sala.salidas:
            destino = esqueleto.obtener(salida.sala_destino)
            nombre = destino.nombre if destino is not None else "sala desconocida"
            linea = (f"   {self._menu.nombre_direccion(salida.direccion):<6} -> {nombre} "
                     f"({salida.sala_destino})")
            puerta = esqueleto.puerta(sala.id, salida.direccion)
            if puerta is not None and puerta.esta_cerrada():
                if estado.jugador.puede_abrir(puerta):
                    nota = self._color("[cerrada: tienes la llave]", "ok")
                else:
                    nota = self._color(f"[cerrada: falta {self._menu.legible(puerta.llave)}]",
                                       "alerta")
                linea += "   " + nota
            print(linea)

    def _mostrar_enemigos(self, estado, id_sala):
        enemigos = estado.enemigos_en_sala(id_sala)
        self._enemigos_vistos = [e.instancia for e in enemigos]
        if not enemigos:
            print(self._color(" Enemigos", "negrita") + "   ninguno")
            return
        print(self._color(" Enemigos", "negrita"))
        for numero, enemigo in enumerate(enemigos, 1):
            print(f"   {numero}. {enemigo.nombre} {enemigo.instancia:<10} "
                  + self._color(self._barra(enemigo.vida, enemigo.vida_max), "peligro")
                  + f" {enemigo.vida}/{enemigo.vida_max}  {enemigo.comportamiento or ''}")

    def _mostrar_suelo(self, estado, id_sala):
        suelo = estado.suelo(id_sala)
        self._suelo_visto = list(suelo)
        if not suelo:
            print(self._color(" En el suelo", "negrita") + "   nada")
        else:
            print(self._color(" En el suelo", "negrita"))
            for numero, id_objeto in enumerate(suelo, 1):
                print(f"   {numero}. {self._menu.legible(id_objeto)}")
        trampas = estado.trampas_en(id_sala)
        if trampas:
            detalle = ", ".join(f"{self._menu.legible(t.tipo)} "
                                f"({'armada' if t.armada else 'desarmada'})" for t in trampas)
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
        nombres = [o.nombre for o in inventario.obtener_elementos()]
        print(f"      inventario {len(inventario)}/{inventario.capacidad}: "
              + (", ".join(nombres) if nombres else "vacío"))

    def mostrar_resultado(self, comando, mensajes):
        # se muestran en la siguiente pantalla (o al final), así no salen dos veces
        self._nuevos.extend(mensajes)
        for mensaje in mensajes:
            if mensaje.startswith(INICIOS_DE_RECHAZO):
                # un paso de la opción falló: no se sigue con los demás
                self._pendientes = []

    def _mostrar_nuevos(self):
        for mensaje in self._nuevos:
            print(self._color("» " + mensaje, "nuevo"))
        self._nuevos = []

    def mostrar_bitacora(self, mensajes):
        cantidad = "1 mensaje" if len(mensajes) == 1 else f"{len(mensajes)} mensajes"
        print(self._color(" Bitácora", "negrita")
              + self._color(f"   (últimos 20; ahora {cantidad})", "tenue"))
        primero_nuevo = len(mensajes) - len(self._nuevos)
        for i, mensaje in enumerate(mensajes):
            if i >= primero_nuevo:
                print(self._color("  » " + mensaje, "nuevo"))
            else:
                print(self._color("    " + mensaje, "tenue"))
        self._nuevos = []

    # ------------------------------------------------------------ inventario

    def mostrar_objeto_actual(self, objeto):
        if self._pendientes:
            # el cursor se está moviendo por una opción del menú: no hace falta avisar
            return
        if objeto is None:
            print("El inventario está vacío.")
            return
        print(f"Ahora ves: {self._color(objeto.nombre, 'negrita')} ({objeto.clase}, "
              f"peso {objeto.peso}, valor {objeto.valor})"
              + self._color(f"  -> {self._uso(objeto.clase)}", "tenue"))

    def mostrar_inventario_detallado(self, pares):
        print(self._color(" Inventario", "negrita")
              + self._color("   (para ordenarlo: inv peso, inv valor o inv nombre)", "tenue"))
        if not pares:
            print("   (vacío)")
            return
        print(self._color(f"   {'#':>2}  {'Objeto':<30} {'Clase':<20} {'Peso':>4} {'Valor':>6}",
                          "tenue"))
        for numero, (objeto, equipado) in enumerate(pares, 1):
            marca = " [equipado]" if equipado else ""
            print(f"   {numero:>2}  {objeto.nombre + marca:<30} {objeto.clase:<20} "
                  f"{objeto.peso if objeto.peso is not None else '-':>4} "
                  f"{objeto.valor if objeto.valor is not None else '-':>6}")

    def mostrar_ayuda(self):
        print(self._titulo("Cómo jugar"))
        print(AYUDA)

    # ------------------------------------------------------------ final

    def mostrar_fin(self, estado):
        self._pendientes = []
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
    def _color_de(tipo):
        for nombre, estilo in COLOR_DE_OPCION:
            if nombre == tipo:
                return estilo
        return "negrita"

    @staticmethod
    def _barra(actual, maximo, ancho=10):
        if not maximo or maximo <= 0:
            return "[" + "-" * ancho + "]"
        llenos = min(ancho, max(0, round(ancho * max(0, actual) / maximo)))
        return "[" + "#" * llenos + "-" * (ancho - llenos) + "]"

    @staticmethod
    def _uso(clase):
        for nombre, uso in USOS:
            if nombre == clase:
                return uso
        return "soltar"
