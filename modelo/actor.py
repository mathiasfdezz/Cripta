class Actor:
    """Lo que tienen en común el jugador y los enemigos."""

    def __init__(self, id_actor, sala, vida_max, ataque, defensa, velocidad, vida=None):
        if velocidad <= 0:
            raise ValueError("la velocidad debe ser mayor que 0")
        self.id = id_actor
        self.sala = sala
        self.vida_max = vida_max
        self.vida = vida_max if vida is None else vida
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.proximo_evento = None   # el Evento que tiene programado en la agenda

    def esta_vivo(self):
        return self.vida > 0

    def ataque_efectivo(self):
        return self.ataque

    def defensa_efectiva(self):
        return self.defensa

    def recibir_dano(self, dano):
        self.vida = max(0, self.vida - dano)

    def puede_abrir(self, puerta):
        # sin inventario no hay llaves: solo el jugador abre puertas
        return False

    def __repr__(self):
        return f"{type(self).__name__}({self.id}, sala={self.sala}, vida={self.vida})"