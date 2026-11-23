import pygame
from classes.game_object import game_object
from constants import LARGURA, CHAO_Y

class Inimigo(game_object):
    def __init__(self, velocidade_extra=0):
        imagem = pygame.image.load("inimigos1_1.png").convert_alpha()
        imagem = pygame.transform.scale(imagem, (96, 96))
        super().__init__(imagem)

        # nasce fora da tela, à direita, em cima do chão
        self.rect.left = LARGURA
        self.rect.bottom = CHAO_Y

        self.velocidade_extra = velocidade_extra

    def atualizar(self, velocidade_mundo):
        # o mundo anda para a esquerda, o inimigo acompanha
        self.rect.x -= velocidade_mundo + self.velocidade_extra

    def saiu_da_tela(self):
        return self.rect.right < 0