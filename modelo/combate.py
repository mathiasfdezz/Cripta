from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoAtaque:
    atacante: object
    defensor: object
    dano: int
    murio: bool   # el defensor quedó sin vida con este golpe


def puede_atacar(atacante, defensor):
    """Solo se combate entre actores vivos que están en la misma sala."""
    return (atacante is not defensor
            and atacante.esta_vivo() and defensor.esta_vivo()
            and atacante.sala == defensor.sala)


def calcular_dano(atacante, defensor, azar):
    """azar es el random.Random de la partida: cada golpe consume un randint."""
    return max(1, atacante.ataque_efectivo() + azar.randint(0, 4) - defensor.defensa_efectiva())


def atacar(atacante, defensor, azar):
    if not puede_atacar(atacante, defensor):
        raise ValueError("no se puede atacar: ambos deben estar vivos y en la misma sala")
    dano = calcular_dano(atacante, defensor, azar)
    defensor.recibir_dano(dano)
    return ResultadoAtaque(atacante, defensor, dano, not defensor.esta_vivo())