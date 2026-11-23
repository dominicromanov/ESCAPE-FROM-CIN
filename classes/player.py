import pygame

# 1. Inicializando o Pygame
pygame.init()


# 2. Configurações da janela
LARGURA = 1280
ALTURA = 720

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("ESCAPE-FROM-CIN")

# Controla a velocidade de atualização do jogo
relogio = pygame.time.Clock()


# 3. Criando a classe Player
class Player:

    # Inicializa o personagem
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocidade = 5

        # Define o tamanho da bola
        self.raio = 20

    # Movimenta o personagem
    def movimentar(self, teclas):

        # Movimento para a esquerda
        if teclas[pygame.K_a]:
            self.x -= self.velocidade

        # Movimento para a direita
        if teclas[pygame.K_d]:
            self.x += self.velocidade

        # Movimento para cima
        if teclas[pygame.K_w]:
            self.y -= self.velocidade

        # Movimento para baixo
        if teclas[pygame.K_s]:
            self.y += self.velocidade

    # Desenha o personagem na tela
    def desenhar(self):

        pygame.draw.circle(tela, (50, 150, 255), (self.x, self.y), self.raio)


# 4. Criando o objeto Player
player = Player(640, 360)


# 5. Iniciando o Game Loop
executando = True

while executando:

    # Verifica se o usuário fechou a janela
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            executando = False

    # Verifica quais teclas estão pressionadas
    teclas = pygame.key.get_pressed()

    # Atualiza a movimentação do personagem
    player.movimentar(teclas)

    # Pinta o fundo da tela
    tela.fill((30, 30, 30))

    # Desenha o personagem
    player.desenhar()

    # Atualiza a imagem da janela
    pygame.display.flip()

    # Mantém o jogo em 60 FPS
    relogio.tick(60)


# 6. Encerra o Pygame
pygame.quit()
