from .inimigo import Inimigo


class Humanoide(Inimigo):
    """Inimigo terrestre: anda, para, espera 0,5 s e ataca."""
    PASTA = "humanoide"
    TOTAL_FRAMES = {"WALK": 4, "ATTACK": 3, "FALL": 1}

    ALTURA_ALVO = 140           # parecido com o player (hitbox dele é 140)
    VIDA_MAXIMA = 75            # 3 socos do player (dano 25)
    DANO = 1
    DISTANCIA_DETECCAO = 110    # a que distância "enxerga" o player
    ALCANCE_ATAQUE = 40         # o braço/arma alcança mais que o robô
    FRAMES_ATIVOS_ATAQUE = (1, 2)  # ajuste conforme a arte (índices contam de 0)