import math
from .inimigo import Inimigo
from constants import CHAO_Y


class Drone(Inimigo):
    """Inimigo voador: voa em onda, mira no player, espera 0,5 s e ataca."""
    PASTA = "drone"
    TOTAL_FRAMES = {"WALK": 4, "ATTACK": 3, "FALL": 2}

    ALTURA_ALVO = 50
    VIDA_MAXIMA = 50
    DANO = 1
    DISTANCIA_DETECCAO = 150       # só horizontal; o drone avisa de mais longe
    ALCANCE_ATAQUE = 20
    FRAMES_ATIVOS_ATAQUE = (1, 2)  # ajuste conforme a arte do ataque

    # --- voo ---
    ALTURA_PADRAO = 400            # linha do meio da onda (centro do drone, em y)
    AMPLITUDE = 80                 # quantos pixels sobe e desce
    FREQUENCIA = 0.05              # maior = oscila mais rápido
    VELOCIDADE_MIRA = 3            # px/frame ao descer até o player
    VELOCIDADE_RETORNO = 2         # px/frame ao voltar para a altura padrão
    VELOCIDADE_QUEDA = 10          # px/frame na animação de morte

    def __init__(self, velocidade_extra=0):
        super().__init__(velocidade_extra)
        self.tempo = 0
        self.altura_base = float(self.ALTURA_PADRAO)
        self.rect.centery = self.ALTURA_PADRAO

    # ---------- detecção horizontal ----------
    def _viu(self, alvo):
        zona = self.rect.inflate(self.DISTANCIA_DETECCAO * 2, 0)
        return zona.left < alvo.right and zona.right > alvo.left

    # ---------- continuidade da onda ----------
    def _mudar_estado(self, novo):
        super()._mudar_estado(novo)
        if novo == "ANDANDO":
            # recomeça a onda a partir da altura atual (sem pulo)
            self.altura_base = self.rect.centery - math.sin(self.tempo * self.FREQUENCIA) * self.AMPLITUDE

    # ---------- movimento ----------
    def atualizar(self, velocidade_mundo, alvo=None):
        super().atualizar(velocidade_mundo, alvo)  # estados, x, animação

        if self.estado == "ANDANDO":
            self.tempo += 1
            # a linha do meio volta aos poucos para a altura padrão
            if self.altura_base < self.ALTURA_PADRAO:
                self.altura_base = min(self.ALTURA_PADRAO, self.altura_base + self.VELOCIDADE_RETORNO)
            elif self.altura_base > self.ALTURA_PADRAO:
                self.altura_base = max(self.ALTURA_PADRAO, self.altura_base - self.VELOCIDADE_RETORNO)
            deslocamento = math.sin(self.tempo * self.FREQUENCIA) * self.AMPLITUDE
            self.rect.centery = round(self.altura_base + deslocamento)

        elif self.estado == "PREPARANDO" and alvo is not None:
            # desce até a altura do player
            if self.rect.centery < alvo.centery:
                self.rect.centery = min(alvo.centery, self.rect.centery + self.VELOCIDADE_MIRA)
            elif self.rect.centery > alvo.centery:
                self.rect.centery = max(alvo.centery, self.rect.centery - self.VELOCIDADE_MIRA)

        elif self.estado == "MORRENDO":
            self.rect.bottom = min(CHAO_Y, self.rect.bottom + self.VELOCIDADE_QUEDA)
        # em ATACANDO ele fica parado na altura em que estava (ataque "comprometido")