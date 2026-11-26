import pygame
from constants import LARGURA, ALTURA, FPS
from classes.inimigos import Inimigo
from sys import exit

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
relogio = pygame.time.Clock()
pygame.display.set_caption('Escape from CIn')   #nome da janela

velocidade_mundo = 3
inimigo = Inimigo()          # o primeiro nasce já no começo
tempo_espera = 0             # contador de frames da espera
ESPERA_FRAMES = 2 * FPS      # 2 segundos = 120 frames

rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    if inimigo is not None:
        inimigo.atualizar(velocidade_mundo)

        if inimigo.saiu_da_tela():
            inimigo = None       # remove o inimigo
            tempo_espera = 0     # começa a contar a espera
    else:
        tempo_espera += 1
        if tempo_espera >= ESPERA_FRAMES:
            inimigo = Inimigo()  # nasce o próximo

    tela.fill((30, 30, 50))
    if inimigo is not None:
        inimigo.desenhar(tela)

    pygame.display.flip()
    relogio.tick(FPS)

pygame.quit()
exit()