from pathlib import Path
import pygame

from classes.game_object import GameObject
from constants import LARGURA, CHAO_Y, FPS


class Inimigo(GameObject):
    """Base de todos os inimigos. Cada inimigo só sobrescreve as configurações."""

    # --- configurações (a subclasse sobrescreve) ---
    PASTA = None
    TOTAL_FRAMES = {"WALK": 4, "ATTACK": 4, "FALL": 2}
    ALTURA_ALVO = 60
    VIDA_MAXIMA = 50
    DANO = 1
    DISTANCIA_DETECCAO = 40
    ALCANCE_ATAQUE = 30
    FRAMES_ATIVOS_ATAQUE = (2, 3)
    ESPERA_ATAQUE = FPS // 2        # 0,5 s antes de atacar
    RECARGA = FPS                   # 1 s sem atacar depois de um ataque
    INTERVALO = {"WALK": 8, "ATTACK": 8, "FALL": 12}  # frames do jogo por frame de animação
    VIRAR_SPRITES = False           # True se a arte olhar para o lado errado

    ANIMACAO_DO_ESTADO = {
        "ANDANDO": "WALK",
        "PREPARANDO": "WALK",
        "ATACANDO": "ATTACK",
        "MORRENDO": "FALL",
    }

    _cache = {}  # sprites carregados 1 vez só e compartilhados entre os inimigos

    # ---------- carregamento ----------
    @classmethod
    def _carregar_animacoes(cls):
        if cls.PASTA in Inimigo._cache:
            return Inimigo._cache[cls.PASTA]

        raiz = Path(__file__).resolve().parent.parent.parent
        pasta = raiz / "assets" / "inimigos" / cls.PASTA

        recortados = {}
        for estado, total in cls.TOTAL_FRAMES.items():
            lista = []
            for i in range(1, total + 1):
                img = pygame.image.load(str(pasta / estado / f"{estado}_{i:02d}.png")).convert_alpha()
                img = img.subsurface(img.get_bounding_rect()).copy()  # tira margem transparente
                lista.append(img)
            recortados[estado] = lista

        # mesma escala para todos os frames (senão o robô "encolhe" ao atacar)
        escala = cls.ALTURA_ALVO / recortados["WALK"][0].get_height()
        animacoes = {}
        for estado, lista in recortados.items():
            animacoes[estado] = []
            for img in lista:
                tamanho = (max(1, round(img.get_width() * escala)),
                           max(1, round(img.get_height() * escala)))
                img = pygame.transform.scale(img, tamanho)
                if cls.VIRAR_SPRITES:
                    img = pygame.transform.flip(img, True, False)
                animacoes[estado].append(img)

        Inimigo._cache[cls.PASTA] = animacoes
        return animacoes

    # ---------- criação ----------
    def __init__(self, velocidade_extra=0):
        self.animacoes = self._carregar_animacoes()
        super().__init__(self.animacoes["WALK"][0])  # rect = tamanho total do robô

        self.rect.left = LARGURA          # nasce fora da tela, à direita
        self.rect.bottom = CHAO_Y
        self.velocidade_extra = velocidade_extra

        self.vida = self.VIDA_MAXIMA
        self.estado = "ANDANDO"
        self.indice_frame = 0
        self.contador_anim = 0
        self.contador_estado = 0
        self.recarga = 0
        self.ja_acertou = False
        self.removivel = False

    # ---------- propriedades ----------
    @property
    def esta_vivo(self):
        return self.vida > 0

    # ---------- lógica principal ----------
    def atualizar(self, velocidade_mundo, alvo=None):
        """alvo = pygame.Rect do player (ou None)."""
        if self.estado == "ANDANDO":
            self.rect.x -= velocidade_mundo + self.velocidade_extra
            if self.recarga > 0:
                self.recarga -= 1
            elif alvo is not None and self._viu(alvo):
                self._mudar_estado("PREPARANDO")
        else:
            # parado: só acompanha o cenário
            self.rect.x -= velocidade_mundo
            if self.estado == "PREPARANDO":
                self.contador_estado += 1
                if self.contador_estado >= self.ESPERA_ATAQUE:
                    self._mudar_estado("ATACANDO")

        self._avancar_animacao()

    def _viu(self, alvo):
        zona = self.rect.inflate(self.DISTANCIA_DETECCAO * 2, 0)  # mesma altura do robô
        return zona.colliderect(alvo)

    def _mudar_estado(self, novo):
        self.estado = novo
        self.indice_frame = 0
        self.contador_anim = 0
        self.contador_estado = 0
        if novo == "ATACANDO":
            self.ja_acertou = False

    def _avancar_animacao(self):
        nome = self.ANIMACAO_DO_ESTADO[self.estado]
        total = len(self.animacoes[nome])

        if self.estado != "PREPARANDO":  # na espera fica congelado no 1º frame
            self.contador_anim += 1
            if self.contador_anim >= self.INTERVALO[nome]:
                self.contador_anim = 0
                if self.indice_frame < total - 1:
                    self.indice_frame += 1
                elif self.estado == "ANDANDO":
                    self.indice_frame = 0
                elif self.estado == "ATACANDO":
                    self._mudar_estado("ANDANDO")
                    self.recarga = self.RECARGA
                elif self.estado == "MORRENDO":
                    self.removivel = True

        nome = self.ANIMACAO_DO_ESTADO[self.estado]  # o estado pode ter mudado
        frames = self.animacoes[nome]
        self.imagem = frames[min(self.indice_frame, len(frames) - 1)]

    # ---------- combate ----------
    def obter_dados_ataque(self):
        
        ativo = (
            self.estado == "ATACANDO"
            and self.indice_frame in self.FRAMES_ATIVOS_ATAQUE
            and not self.ja_acertou
        )
        hitbox = None
        if ativo:
            hitbox = pygame.Rect(
                self.rect.left - self.ALCANCE_ATAQUE, self.rect.top,
                self.rect.width + self.ALCANCE_ATAQUE, self.rect.height,
            )
        return {"ativo": ativo, "hitbox": hitbox, "dano": self.DANO}

    def registrar_acerto(self):
        """Chame quando o ataque acertou o player (evita dano repetido no mesmo golpe)."""
        self.ja_acertou = True

    def receber_dano(self, quantidade=25):
        if not self.esta_vivo:
            return True
        self.vida = max(0, self.vida - quantidade)
        if not self.esta_vivo:
            self._mudar_estado("MORRENDO")
        return not self.esta_vivo

    # ---------- remoção ----------
    def saiu_da_tela(self):
        return self.rect.right < 0

    def deve_remover(self):
        return self.saiu_da_tela() or self.removivel

    # ---------- desenho ----------
    def desenhar(self, tela, depuracao=False):
        x = self.rect.centerx - self.imagem.get_width() // 2
        y = self.rect.bottom - self.imagem.get_height()
        tela.blit(self.imagem, (x, y))
        self._desenhar_barra_vida(tela, y)

        if depuracao:
            pygame.draw.rect(tela, (0, 255, 0), self.rect, 2)
            dados = self.obter_dados_ataque()
            if dados["hitbox"] is not None:
                pygame.draw.rect(tela, (255, 50, 50), dados["hitbox"], 2)

    def _desenhar_barra_vida(self, tela, topo_sprite):
        if not self.esta_vivo or self.vida == self.VIDA_MAXIMA:
            return  # só aparece depois de apanhar
        largura = self.rect.width
        barra = pygame.Rect(self.rect.left, topo_sprite - 10, largura, 5)
        pygame.draw.rect(tela, (60, 20, 20), barra)
        preenchido = barra.copy()
        preenchido.width = int(largura * self.vida / self.VIDA_MAXIMA)
        pygame.draw.rect(tela, (220, 50, 50), preenchido)