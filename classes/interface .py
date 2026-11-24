import os
import pygame

from constants import LARGURA, IMAGES_PATH


class Interface:
    def __init__(self):
        self.vidas = 3
        self.vidas_maximas = 3
        self.itens_vida = 0
        self.itens_velocidade = 0
        self.letras = {"C": False, "I": False, "N": False}
        self.inicio = pygame.time.get_ticks()

        pasta_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_imagens = os.path.join(pasta_projeto, IMAGES_PATH)

        self.fonte = pygame.font.Font(None, 30)
        self.fonte_pequena = pygame.font.Font(None, 23)
        self.icones = {}

        nomes = {
            "coracao_cheio": "coracao_cheio.png",
            "coracao_vazio": "coracao_vazio.png",
            "raio": "raio.png",
            "relogio": "relogio.png",
            "letra_c": "letra_c.png",
            "letra_i": "letra_i.png",
            "letra_n": "letra_n.png"
        }

        for nome, arquivo in nomes.items():
            caminho = os.path.join(pasta_imagens, arquivo)
            if os.path.exists(caminho):
                imagem = pygame.image.load(caminho).convert_alpha()
                self.icones[nome] = pygame.transform.smoothscale(imagem, (25, 25))

    def atualizar(self):
        self.vidas = max(0, min(self.vidas, self.vidas_maximas))

    def _texto(self, tela, texto, x, y, fonte=None, cor=(245, 240, 255)):
        if fonte is None:
            fonte = self.fonte
        imagem = fonte.render(str(texto), True, cor)
        tela.blit(imagem, (x, y))

    def _icone(self, tela, nome, x, y, cor, letra=None):
        if nome in self.icones:
            tela.blit(self.icones[nome], (x, y))
        elif letra is not None:
            pygame.draw.rect(tela, cor, (x, y, 25, 25), border_radius=5)
            imagem = self.fonte_pequena.render(letra, True, (255, 255, 255))
            tela.blit(imagem, imagem.get_rect(center=(x + 12, y + 12)))
        else:
            pygame.draw.circle(tela, cor, (x + 12, y + 12), 10)

    def desenhar(self, tela):
        self.atualizar()

        largura = 1080
        altura = 76
        x = (LARGURA - largura) // 2
        y = 18

        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(painel, (28, 20, 48, 225), (0, 0, largura, altura), border_radius=12)
        pygame.draw.rect(painel, (164, 132, 220, 255), (0, 0, largura, altura), 2, border_radius=12)
        tela.blit(painel, (x, y))

        for divisao in (220, 430, 650, 860):
            pygame.draw.line(tela, (112, 91, 151), (x + divisao, y + 12), (x + divisao, y + 64), 2)

        self._texto(tela, "VIDAS", x + 18, y + 8, self.fonte_pequena)
        for i in range(self.vidas_maximas):
            nome = "coracao_cheio" if i < self.vidas else "coracao_vazio"
            cor = (235, 75, 115) if i < self.vidas else (95, 82, 112)
            self._icone(tela, nome, x + 22 + i * 34, y + 35, cor)

        segundos = (pygame.time.get_ticks() - self.inicio) // 1000
        minutos = segundos // 60
        segundos = segundos % 60
        self._texto(tela, "TEMPO", x + 242, y + 8, self.fonte_pequena)
        self._icone(tela, "relogio", x + 245, y + 36, (235, 205, 110))
        self._texto(tela, f"{minutos:02}:{segundos:02}", x + 280, y + 37)

        self._texto(tela, "COLETÁVEIS", x + 450, y + 8, self.fonte_pequena)
        self._icone(tela, "coracao_cheio", x + 455, y + 36, (235, 75, 115))
        self._texto(tela, self.itens_vida, x + 485, y + 38, self.fonte_pequena)
        self._icone(tela, "raio", x + 535, y + 36, (245, 205, 75))
        self._texto(tela, self.itens_velocidade, x + 565, y + 38, self.fonte_pequena)

        self._texto(tela, "LETRAS", x + 675, y + 8, self.fonte_pequena)
        for i, letra in enumerate(("C", "I", "N")):
            cor = (119, 190, 145) if self.letras[letra] else (85, 72, 111)
            nome = f"letra_{letra.lower()}"
            self._icone(tela, nome, x + 680 + i * 38, y + 35, cor, letra)

        self._texto(tela, "OBJETIVO", x + 885, y + 8, self.fonte_pequena)
        coletadas = sum(self.letras.values())
        self._texto(tela, f"{coletadas}/3 letras", x + 885, y + 38, self.fonte_pequena)
