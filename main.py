import pygame
from constants import LARGURA, ALTURA, FPS
from classes.inimigo import Aspirador
from classes.player import Player
from classes.interface import Interface
from classes.cenario import Cenario
from sys import exit

class Main:

    def __init__(self, inimigo, player, interface, tela):
        self.inimigo = inimigo
        self.player = player
        self.interface = interface
        self.tela = tela
        self.velocidade_mundo = 3
        self.tempo_espera = 0
        self.ESPERA_FRAMES = FPS * 2
        self.cenario1 = Cenario(0, 0)
        self.cenario2 = Cenario(0, 0)
        self.cenario2.rect.x = self.cenario1.rect.right

    def coordena_inimigo(self):
        if self.inimigo is not None:
            self.inimigo.atualizar(self.velocidade_mundo)

            if self.inimigo.saiu_da_tela():
                self.inimigo = None
                self.tempo_espera = 0

        else:
            self.tempo_espera += 1
            if self.tempo_espera >= self.ESPERA_FRAMES:
                self.inimigo = Aspirador()

    def desenhar(self):
        self.cenario1.desenha_cenario(self.tela)
        self.cenario2.desenha_cenario(self.tela)

        if self.inimigo is not None:
            self.inimigo.desenhar(self.tela)

        self.player.desenhar(self.tela)
        self.interface.desenhar(self.tela)

    def atualizar(self, dt):
        self.cenario1.atualizar(self.cenario2)
        self.cenario2.atualizar(self.cenario1)

        self.coordena_inimigo()
        dt = relogio.tick(FPS) / 1000
        self.player.atualizar(pygame.key.get_pressed(), dt)


pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
enemy = Aspirador()

jogador = Player()
interfaces = Interface()

inicio = Main(enemy, jogador, interfaces, tela)

relogio = pygame.time.Clock()
pygame.display.set_caption('Escape from CIn')  

tempo_espera = 0             

rodando = True
while rodando:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    dt = relogio.tick(FPS)

    inicio.atualizar(dt / 1000)
    inicio.desenhar()
    pygame.display.flip()


pygame.quit()
exit()