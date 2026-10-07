AYUDA = """
Comandos:
  n / s / e / o        moverse (100)
  abrir <dir>          abrir una puerta con llave (50)
  atacar [instancia]   atacar a un enemigo de la sala (100)
  esperar              dejar pasar el turno (100)
  recoger [id]         recoger un objeto del suelo (25)
  soltar               soltar el objeto que estás viendo (25)
  equipar              equipar el arma o armadura que estás viendo (50)
  usar                 usar la poción, antídoto o antorcha que estás viendo (50)
  sig / ant            ver el objeto siguiente / anterior del inventario
  inv [peso|valor|nombre]   ver el inventario, ordenado si se indica
  deshacer             usar un pergamino de retroceso
  ayuda                ver esta lista
  salir                terminar la sesión
"""


class Consola:

    def mostrar_mensaje(self, texto):
        print(texto)

    def mostrar_objeto_actual(self, objeto):
        if objeto is None:
            print("No hay objeto seleccionado.")
            return
        print(f"Objeto actual: {objeto.nombre} | Peso: {objeto.peso} | Valor: {objeto.valor}")

    def mostrar_objeto_soltado(self, objeto):
        if objeto is None:
            print("No hay objeto para soltar.")
            return
        print(f"Objeto soltado: {objeto.nombre}")

    def mostrar_objeto_equipado(self, objeto):
        if objeto is None:
            print("No hay objeto para equipar.")
            return
        print(f"Objeto equipado: {objeto.nombre}")

    def mostrar_inventario_detallado(self, pares):
        print("\n--- Inventario ---")
        for objeto, equipado in pares:
            marca = " [equipado]" if equipado else ""
            print(f"{objeto.nombre}{marca} | Peso: {objeto.peso} | Valor: {objeto.valor}")
        print("------------------")

    def mostrar_bitacora(self, mensajes):
        print("\n--- Ultimos mensajes ---")
        for mensaje in mensajes:
            print(mensaje)
        print("------------------------")

    # ------------------------------------------------------------- partida

    def mostrar_partida(self, estado, esqueleto, mensajes):
        jugador = estado.jugador
        sala = esqueleto.obtener(jugador.sala)
        print(f"\n===== Sala {sala.id}: {sala.nombre}   (tiempo {estado.tiempo}) =====")
        salidas = []
        for salida in sala.salidas:
            cerrada = esqueleto.puerta(sala.id, salida.direccion).esta_cerrada()
            salidas.append(f"{salida.direccion}->{salida.sala_destino}" + (" [cerrada]" if cerrada else ""))
        print("Salidas:  " + ("  ".join(salidas) if salidas else "ninguna"))
        enemigos = [f"{e.nombre} {e.instancia} ({e.vida}/{e.vida_max})"
                    for e in estado.enemigos_en_sala(sala.id)]
        print("Enemigos: " + (", ".join(enemigos) if enemigos else "ninguno"))
        suelo = estado.suelo(sala.id)
        print("Suelo:    " + (", ".join(suelo) if suelo else "nada"))
        efectos = []
        if estado.antorcha_hasta is not None:
            efectos.append(f"antorcha encendida hasta t={estado.antorcha_hasta}")
        print(f"Tú:       vida {jugador.vida}/{jugador.vida_max}  ataque {jugador.ataque_efectivo()}"
              f"  defensa {jugador.defensa_efectiva()}  velocidad {jugador.velocidad}"
              + (f"  | {', '.join(efectos)}" if efectos else ""))
        inventario = jugador.inventario
        actual = inventario.obtener_actual()
        print(f"Inventario: {len(inventario)}/{inventario.capacidad}"
              + (f", viendo: {actual.nombre}" if actual is not None else "")
              + f"   Pergaminos: {inventario.cantidad_pergaminos()}")
        self.mostrar_bitacora(mensajes)

    def mostrar_resultado(self, comando, mensajes):
        for mensaje in mensajes:
            print(mensaje)

    def mostrar_ayuda(self):
        print(AYUDA)

    def pedir_comando(self):
        try:
            return input("> ")
        except EOFError:
            return None

    def pedir_nombre(self):
        try:
            return input("Tu nombre para la tabla de puntajes: ")
        except EOFError:
            return ""

    def mostrar_fin(self, estado):
        if estado.resultado == "victoria":
            print("\n*** ¡Victoria! ***")
        elif estado.resultado == "derrota":
            print("\n*** Derrota ***")
        else:
            print("\nPartida sin terminar.")
        print(f"Acciones: {estado.acciones}  Enemigos derrotados: {estado.enemigos_derrotados}"
              f"  Tiempo final: {estado.tiempo}")

    def mostrar_puntajes(self, registros):
        print("\n--- Tabla de puntajes ---")
        for registro in registros[:10]:
            print(f"{registro.nombre:<15} {registro.cripta_id} v{registro.version_cripta}"
                  f"  {registro.resultado:<8} acciones {registro.acciones:<4}"
                  f" enemigos {registro.enemigos_derrotados:<3} tiempo {registro.tiempo_final}")

    def mostrar_reporte(self, solicitudes, presupuesto, aciertos, fallos):
        print(f"\nSolicitudes de red: {solicitudes}/{presupuesto}"
              f"   Caché: {aciertos} aciertos, {fallos} fallos")
