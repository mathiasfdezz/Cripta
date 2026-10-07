class Evento:
    def __init__(self, tipo, objetivo, dato=None):
        # tipo: qué va a pasar ("accion", "veneno", "rearme_trampa", ...)
        # objetivo: a quién le pasa ("jugador", "e-201", "t-17", ...)
        self.tipo = tipo
        self.objetivo = objetivo
        # dato: lo que el evento necesita al ejecutarse (por ejemplo, cuánta velocidad devolver)
        self.dato = dato
        # los llena la agenda al programar el evento
        self.tiempo_siguiente = None
        self.secuencia = None
        # cancelado: la agenda lo ignora cuando llega a la raíz del heap
        self.cancelado = False
        # en_agenda: sigue dentro del heap (aún no se ha sacado ni descartado)
        self.en_agenda = False

    def __repr__(self):
        return f"Evento({self.tipo}, {self.objetivo})"