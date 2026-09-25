class Evento:
    def __init__(self, tipo, objetivo):
        # tipo: qué va a pasar ("accion", "veneno", "rearme_trampa", ...)
        # objetivo: a quién le pasa ("jugador", "e-201", "t-17", ...)
        self.tipo = tipo
        self.objetivo = objetivo

    def __repr__(self):
        return f"Evento({self.tipo}, {self.objetivo})"
