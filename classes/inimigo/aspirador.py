from .inimigo import Inimigo


class Aspirador(Inimigo):
    """Inimigo 1: anda, para, espera 0,5 s e ataca."""
    PASTA = "aspirador"
    TOTAL_FRAMES = {"WALK": 4, "ATTACK": 4, "FALL": 2}

    ALTURA_ALVO = 60            # altura do robô na tela, em pixels
    VIDA_MAXIMA = 50            # 2 socos do player (dano 25)
    DANO = 1                    # vidas que tira do player
    DISTANCIA_DETECCAO = 40     # a que distância "enxerga" o player
    ALCANCE_ATAQUE = 30         # quanto o ataque passa da frente do robô
    FRAMES_ATIVOS_ATAQUE = (2, 3)  # frames do ataque que machucam (o arco branco)