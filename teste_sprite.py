import sys
import pygame

# 1. Inicializa o Pygame
pygame.init()

# 2. Configurações da janela (1280x720) e do relógio (60 FPS)
LARGURA = 1280
ALTURA = 720
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Movimentação Horizontal e Animação RUN - ESCAPE-FROM-CIN")
relogio = pygame.time.Clock()

# 3. Função auxiliar para carregar sprites com transparência
def carregar_sprites(caminhos):
    """Carrega uma lista de caminhos de arquivos e retorna superfícies com convert_alpha()."""
    return [pygame.image.load(caminho).convert_alpha() for caminho in caminhos]

# Carregamento dos frames de STOP (3 frames)
caminhos_stop = [
    f"assets/player/STOP/sprite_1_01_0{i}.png" for i in range(1, 4)
]
frames_stop = carregar_sprites(caminhos_stop)

# Carregamento dos frames de RUN (7 frames)
caminhos_run = [
    f"assets/player/RUN/sprite_2_01_0{i}.png" for i in range(1, 8)
]
frames_run = carregar_sprites(caminhos_run)

# Dicionário contendo as animações disponíveis
animacoes = {
    "STOP": frames_stop,
    "RUN": frames_run
}

# 4. Variáveis de estado e posição do personagem
posicao_x = 100.0   # Posição horizontal (ponto flutuante para precisão com delta time)
posicao_y = 100     # Eixo vertical fixo em 100
velocidade_pixels_por_segundo = 300.0  # Equivalente a 5 pixels por frame a 60 FPS (5 * 60)

olhando_para_esquerda = False  # Orientação do personagem (True = esquerda, False = direita)
estado_atual = "STOP"          # Estado inicial da animação ("STOP" ou "RUN")

# 5. Variáveis de controle de animação
indice_frame = 0
intervalo_animacao_ms = 120  # Intervalo de aproximadamente 120 ms entre cada frame
ultimo_tempo_animacao = pygame.time.get_ticks()

# Cor de fundo para visualização
COR_FUNDO = (30, 30, 30)

# 6. Game Loop
rodando = True
while rodando:
    # dt: tempo decorrido no frame em segundos para cálculo de movimento independente de FPS
    dt = relogio.tick(60) / 1000.0

    # Tratamento de eventos (permite fechar a janela normalmente)
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # Leitura contínua das teclas pressionadas
    teclas = pygame.key.get_pressed()
    movimento_horizontal = 0

    if teclas[pygame.K_a]:
        movimento_horizontal -= 1
    if teclas[pygame.K_d]:
        movimento_horizontal += 1

    # Atualização de estado (STOP ou RUN) e orientação
    if movimento_horizontal != 0:
        novo_estado = "RUN"
        if movimento_horizontal < 0:
            olhando_para_esquerda = True
        elif movimento_horizontal > 0:
            olhando_para_esquerda = False
    else:
        novo_estado = "STOP"

    # Se mudou de estado (ex: de STOP para RUN ou vice-versa), reinicia o índice da animação
    if novo_estado != estado_atual:
        estado_atual = novo_estado
        indice_frame = 0
        ultimo_tempo_animacao = pygame.time.get_ticks()

    # Atualização da posição com ajuste ao delta time (independente de oscilações de FPS)
    posicao_x += movimento_horizontal * velocidade_pixels_por_segundo * dt

    # Controle de animação por tempo (get_ticks)
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - ultimo_tempo_animacao >= intervalo_animacao_ms:
        frames_lista = animacoes[estado_atual]
        indice_frame = (indice_frame + 1) % len(frames_lista)
        ultimo_tempo_animacao = tempo_atual

    # Obtém o frame atual da animação correspondente
    frame_atual = animacoes[estado_atual][indice_frame]

    # Espelha o sprite horizontalmente caso esteja olhando para a esquerda
    if olhando_para_esquerda:
        frame_para_desenhar = pygame.transform.flip(frame_atual, True, False)
    else:
        frame_para_desenhar = frame_atual

    # Limita o personagem dentro das bordas da janela
    largura_sprite = frame_para_desenhar.get_width()
    if posicao_x < 0:
        posicao_x = 0
    elif posicao_x > LARGURA - largura_sprite:
        posicao_x = LARGURA - largura_sprite

    # Renderização na tela
    TELA.fill(COR_FUNDO)
    TELA.blit(frame_para_desenhar, (int(posicao_x), posicao_y))
    pygame.display.flip()

# Encerra o Pygame e o programa
pygame.quit()
sys.exit()
