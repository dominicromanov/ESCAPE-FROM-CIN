import sys
import pygame
from classes.player import Player

# 1. Inicializa o Pygame
pygame.init()

# 2. Configurações da janela (1280x720) e do relógio (60 FPS)
LARGURA = 1280
ALTURA = 720
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Teste Independente - Classe Player (ESCAPE-FROM-CIN)")
relogio = pygame.time.Clock()

# Fonte para interface de depuração e instruções
fonte = pygame.font.SysFont("Arial", 18)

# 3. Criação da instância do Player
player = Player(x=200, y=200)

# Plataformas e obstáculos de teste (usando pygame.Rect)
plataformas_teste = [
    pygame.Rect(0, 620, LARGURA, 100),   # Chão principal
    pygame.Rect(420, 480, 220, 30),      # Plataforma elevada 1
    pygame.Rect(740, 380, 220, 30),      # Plataforma elevada 2
    pygame.Rect(1020, 480, 50, 140),     # Parede lateral
    pygame.Rect(160, 350, 180, 30),      # Teto baixo para testar impacto superior
]

# Alternância do modo de depuração (tecla H)
modo_depuracao = True

# Cores
COR_FUNDO = (25, 25, 30)
COR_PLATAFORMA = (70, 75, 90)
COR_BORDA_PLATAFORMA = (120, 130, 150)
COR_TEXTO = (230, 230, 230)

# 4. Game Loop principal do teste
rodando = True
while rodando:
    dt = relogio.tick(60) / 1000.0

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_h:
                modo_depuracao = not modo_depuracao
            elif evento.key == pygame.K_k:
                # Simula 1 dano (respeitando i-frames) para testar as 3 vidas
                player.receber_dano(1)
            elif evento.key == pygame.K_m:
                # Zera as vidas imediatamente para testar a animação DEAD
                player.vida = 1
                player.ultimo_dano_tempo = -player.duracao_invulnerabilidade_ms
                player.receber_dano(1)
            elif evento.key == pygame.K_r:
                # Reinicia o personagem
                player = Player(x=200, y=200)

    teclas = pygame.key.get_pressed()

    player.atualizar(
        teclas=teclas,
        dt=dt,
        largura_tela=LARGURA,
        altura_tela=ALTURA,
        plataformas=plataformas_teste,
    )

    TELA.fill(COR_FUNDO)

    # Desenha todas as plataformas de teste
    for plat in plataformas_teste:
        pygame.draw.rect(TELA, COR_PLATAFORMA, plat)
        pygame.draw.rect(TELA, COR_BORDA_PLATAFORMA, plat, 2)

    player.desenhar(TELA, depuracao=modo_depuracao)

    dados_ataque = player.obter_dados_ataque()
    linhas_info = [
        "Controles: [A/D] Mover | [S/BAIXO] Agachar | [W/ESPACO] Pular | [J/F] Atacar | [H] Hitbox | [K] Dano | [M] Morrer | [R] Reset",
        f"Movimento: {player.estado_movimento} | Animacao: {player.estado_animacao} (Frame {player.indice_frame + 1}) | Agachado: {player.agachado} | Vivo: {player.esta_vivo}",
        f"Pos: X={player.x:.1f}, Y={player.y:.1f} | Altura Rect: {player.rect.height} | Vel Y={player.velocidade_vertical:.1f} | No Chao: {player.no_chao}",
        f"Vida: {player.vida}/{player.vida_maxima} | Ataque #{dados_ataque['id_ataque']} Ativo: {dados_ataque['ativo']} | Debug (H): {'ON' if modo_depuracao else 'OFF'}",
    ]

    for i, linha in enumerate(linhas_info):
        texto_render = fonte.render(linha, True, COR_TEXTO)
        TELA.blit(texto_render, (20, 20 + i * 24))

    pygame.display.flip()

pygame.quit()
sys.exit()
