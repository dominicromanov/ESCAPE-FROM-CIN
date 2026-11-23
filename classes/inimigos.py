import pygame
from classes.game_object import GameObject
from constants import LARGURA, CHAO_Y, IMAGES_PATH
import os

class Inimigo(GameObject):
    def __init__(self, velocidade_extra=0):
        imagem = pygame.image.load(os.path.join(IMAGES_PATH, "inimigos1_1.png")).convert_alpha() #os.path.join une as strings IMAGES_PATH(pasta das imagens)+
        imagem = pygame.transform.scale(imagem, (96, 96))                                        #e o nome do arquivo png
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