class Controlador:
    def __init__(self, inventario, vista, bitacora=None):
        self.inventario = inventario
        self.vista = vista
        self.bitacora = bitacora

    def _avisar(self, texto):
        if self.bitacora is not None:
            self.bitacora.agregar(texto)
        self.vista.mostrar_mensaje(texto)

    # --- navegacion (no consume tiempo) ---

    def avanzar_inventario(self):
        self.vista.mostrar_objeto_actual(self.inventario.avanzar())

    def retroceder_inventario(self):
        self.vista.mostrar_objeto_actual(self.inventario.retroceder())

    # --- acciones ---

    def soltar_objeto(self):
        objeto = self.inventario.soltar_actual()
        if objeto is None:
            self._avisar("No hay objeto para soltar.")
            return None
        self.vista.mostrar_objeto_soltado(objeto)
        return objeto

    def equipar_objeto(self):
        if self.inventario.esta_vacio():
            self._avisar("El inventario esta vacio.")
            return False
        if not self.inventario.puede_equipar_actual():
            self._avisar("Solo se pueden equipar armas y armaduras.")
            return False
        self.vista.mostrar_objeto_equipado(self.inventario.equipar_actual())
        return True

    def recoger_objeto(self, objeto):
        """Para objetos del suelo. False (sin consumir tiempo) si esta lleno."""
        if self.inventario.esta_lleno():
            self._avisar("Inventario lleno: suelta algo primero.")
            return False
        self.inventario.recoger(objeto)
        self._avisar("Recogiste: " + objeto.nombre)
        return True

    def mostrar_inventario(self):
        self.vista.mostrar_inventario_detallado(self.inventario.vista_detallada())

    def mostrar_inventario_por_peso(self):
        self.vista.mostrar_inventario_detallado(self.inventario.vista_detallada("peso"))

    def mostrar_inventario_por_valor(self):
        self.vista.mostrar_inventario_detallado(self.inventario.vista_detallada("valor"))

    def mostrar_inventario_por_nombre(self):
        self.vista.mostrar_inventario_detallado(self.inventario.vista_detallada("nombre"))

    def mostrar_bitacora(self):
        if self.bitacora is not None:
            self.vista.mostrar_bitacora(self.bitacora.ultimos())
