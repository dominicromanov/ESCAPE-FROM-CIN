import random
import pygame
from constants import LARGURA, ALTURA, FPS
from classes.inimigo import Aspirador, Drone, Humanoide
from classes.player import Player
from classes.interface import Interface
from classes.cenario import Cenario
from utils.colision import Colision  # <-- Importação atualizada
from sys import exit


class Main:
    TIPOS_INIMIGOS = [Aspirador, Drone, Humanoide]
    MAX_INIMIGOS = 3

    def __init__(self, player, interface, tela):
        self.inimigos = []
        self.player = player
        self.interface = interface
        self.tela = tela
        self.velocidade_mundo = 3
        self.tempo_espera = 0
        self.ESPERA_FRAMES = random.randint(FPS, FPS * 3)
        self.cenario1 = Cenario(0, 0)
        self.cenario2 = Cenario(0, 0)
        self.cenario2.rect.x = self.cenario1.rect.right

    def coordena_inimigo(self):
        for inimigo in self.inimigos[:]:
            inimigo.atualizar(self.velocidade_mundo, self.player.rect)
            if inimigo.deve_remover():
                self.inimigos.remove(inimigo)

        self.tempo_espera += 1
        if self.tempo_espera >= self.ESPERA_FRAMES:
            if len(self.inimigos) < self.MAX_INIMIGOS:
                self.inimigos.append(random.choice(self.TIPOS_INIMIGOS)())
            self.tempo_espera = 0
            self.ESPERA_FRAMES = random.randint(FPS, FPS * 3)

    def coordena_colisoes(self):
        for inimigo in self.inimigos:
            colisor = Colision(self.player, inimigo)
            colisor.verificar_ataque_player()
            colisor.verificar_ataque_inimigo()

    def desenhar(self):
        self.cenario1.desenha_cenario(self.tela)
        self.cenario2.desenha_cenario(self.tela)

        for inimigo in self.inimigos:
            inimigo.desenhar(self.tela)

        self.player.desenhar(self.tela)
        self.interface.desenhar(self.tela)

    def atualizar(self, dt):
        self.cenario1.atualizar(self.cenario2)
        self.cenario2.atualizar(self.cenario1)

        self.coordena_inimigo()
        self.player.atualizar(pygame.key.get_pressed(), dt)
        self.coordena_colisoes()
        self.interface.vidas = self.player.vida


pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))

jogador = Player()
interfaces = Interface()

inicio = Main(jogador, interfaces, tela)

relogio = pygame.time.Clock()
pygame.display.set_caption('Escape from CIn')

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