import pygame
from classes.inimigos import Inimigo
from classes.player.player_physics import PlayerPhysics

class Colision:

    def __init__(self, jogador, inimigo):
        self.jogador = jogador
        self.inimigo = inimigo

    # retorna true ou false e apartir disso decidimos o que fazer com a colisão
    def detectar_colisao(self):

        colidiu = pygame.Rect.colliderect(self.jogador.rect, self.inimigo.rect)

        if colidiu:
            return True

        else:
            return False
        
        