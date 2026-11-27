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
        pasta_fontes = os.path.join(pasta_projeto, "assets", "fontes")

        # Fontes
        caminho_fonte = os.path.join(pasta_fontes, "Exo2.ttf")

        self.fonte = pygame.font.Font(caminho_fonte, 25)
        self.fonte.set_bold(True)

        self.fonte_pequena = pygame.font.Font(caminho_fonte, 16)
        self.fonte_pequena.set_bold(True)

        self.fonte_tempo = pygame.font.Font(caminho_fonte, 29)
        self.fonte_tempo.set_bold(True)

        self.fonte_numeros = pygame.font.Font(caminho_fonte, 24)
        self.fonte_numeros.set_bold(True)

        # Icones
        self.icones = {}

        nomes = {
            "coracao_cheio": "coracao_cheio.png",
            "coracao_vazio": "coracao_vazio.png",
            "raio": "raio.png",
            "relogio": "relogio.png",
            "letra_c": "letra_c.png",
            "letra_i": "letra_i.png",
            "letra_n": "letra_n.png",
            "letra_c_apagada": "letra_c_apagada.png",
            "letra_i_apagada": "letra_i_apagada.png",
            "letra_n_apagada": "letra_n_apagada.png",
        }

        for nome, arquivo in nomes.items():
            caminho = os.path.join(pasta_imagens, arquivo)

            if os.path.exists(caminho):
                imagem = pygame.image.load(caminho).convert_alpha()

                if nome.startswith("letra_"):
                    tamanho = (32, 32)
                else:
                    tamanho = (30, 30)

                self.icones[nome] = pygame.transform.smoothscale(imagem, tamanho)

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
            pygame.draw.rect(tela, cor, (x, y, 32, 32), border_radius=5)

            imagem = self.fonte_pequena.render(
                letra, True, (255, 255, 255)
            )

            tela.blit(imagem, imagem.get_rect(center=(x + 16, y + 16)))

        else:
            pygame.draw.circle(tela, cor, (x + 15, y + 15), 13)

    def desenhar(self, tela):
        self.atualizar()

        largura = 1080
        altura = 90

        x = (LARGURA - largura) // 2
        y = 18

        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)

        pygame.draw.rect(
            painel,
            (28, 20, 48, 255),
            (0, 0, largura, altura),
            border_radius=12
        )

        pygame.draw.rect(
            painel,
            (164, 132, 220, 255),
            (0, 0, largura, altura),
            2,
            border_radius=12
        )

        tela.blit(painel, (x, y))

        for divisao in (220, 430, 650, 860):
            pygame.draw.line(
                tela,
                (112, 91, 151),
                (x + divisao, y + 12),
                (x + divisao, y + 78),
                2
            )

        # Vidas
        self._texto(
            tela, "VIDAS", x + 18, y + 8,
            self.fonte_pequena
        )

        for i in range(self.vidas_maximas):
            nome = "coracao_cheio" if i < self.vidas else "coracao_vazio"
            cor = (235, 75, 115) if i < self.vidas else (95, 82, 112)

            self._icone(
                tela, nome,
                x + 22 + i * 36, y + 43,
                cor
            )

        # Cronometro
        segundos = (pygame.time.get_ticks() - self.inicio) // 1000
        minutos = segundos // 60
        segundos = segundos % 60

        self._texto(
            tela, "TEMPO", x + 242, y + 8,
            self.fonte_pequena
        )

        self._icone(
            tela, "relogio",
            x + 245, y + 43,
            (235, 205, 110)
        )

        self._texto(
            tela,
            f"{minutos:02}:{segundos:02}",
            x + 284, y + 42,
            self.fonte_tempo
        )

        # Coletaveis
        self._texto(
            tela, "COLETÁVEIS", x + 450, y + 8,
            self.fonte_pequena
        )

        self._icone(
            tela, "coracao_cheio",
            x + 455, y + 43,
            (235, 75, 115)
        )

        self._texto(
            tela, self.itens_vida,
            x + 491, y + 44,
            self.fonte_numeros
        )

        self._icone(
            tela, "raio",
            x + 555, y + 43,
            (245, 205, 75)
        )

        self._texto(
            tela, self.itens_velocidade,
            x + 591, y + 44,
            self.fonte_numeros
        )

        # Letras CIN (começam apagadas; ficam verdes quando coletadas)
        self._texto(
            tela, "LETRAS", x + 675, y + 8,
            self.fonte_pequena
        )

        for i, letra in enumerate(("C", "I", "N")):
            coletada = self.letras[letra]
            cor = (119, 190, 145) if coletada else (85, 72, 111)

            nome = f"letra_{letra.lower()}"
            if not coletada:
                nome += "_apagada"

            self._icone(
                tela, nome,
                x + 680 + i * 42, y + 42,
                cor, letra
            )

        # Objetivo
        self._texto(
            tela, "OBJETIVO", x + 885, y + 8,
            self.fonte_pequena
        )

        coletadas = sum(self.letras.values())

        self._texto(
            tela,
            f"{coletadas}/3 letras",
            x + 885, y + 40,
            self.fonte
        )
