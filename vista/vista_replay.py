class VistaReplay:
    """Vista no interactiva para --replay: nunca pide nada al usuario, solo
    muestra cada comando reproducido y lo que pasó."""

    def mostrar_partida(self, estado, esqueleto, mensajes):
        pass

    def mostrar_resultado(self, comando, mensajes):
        print(f"> {comando}")
        for mensaje in mensajes:
            print(f"  {mensaje}")

    def mostrar_objeto_actual(self, objeto):
        pass

    def mostrar_inventario_detallado(self, pares):
        pass

    def mostrar_ayuda(self):
        pass

    def mostrar_fin(self, estado):
        print(f"\nResultado: {estado.resultado}. Acciones: {estado.acciones}, "
              f"enemigos derrotados: {estado.enemigos_derrotados}, tiempo final: {estado.tiempo}")

    def mostrar_reporte(self, solicitudes, presupuesto, aciertos, fallos):
        print(f"Solicitudes de red: {solicitudes}/{presupuesto}"
              f"   Caché: {aciertos} aciertos, {fallos} fallos")
