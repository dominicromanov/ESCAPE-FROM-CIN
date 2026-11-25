import sys
import pygame

from constants import LARGURA, ALTURA, FPS, CHAO_Y
from classes.player import Player


def main():
    # 1. Inicializa o Pygame e cria a janela 1280x720
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Teste Visual Isolado — Player (ESCAPE-FROM-CIN)")
    relogio = pygame.time.Clock()

    # Fontes para HUD de depuração e legenda de controles
    fonte_titulo = pygame.font.SysFont("Arial", 20, bold=True)
    fonte_info = pygame.font.SysFont("Arial", 17)

    # 2. Instancia o Player apoiado diretamente no chão padrão CHAO_Y
    player = Player(x=200)
    exibir_hitboxes = True

    # Cores da cena e da interface
    COR_FUNDO = (24, 26, 36)
    COR_CHAO = (56, 62, 80)
    COR_LINHA_CHAO = (130, 145, 180)
    COR_PAINEL = (18, 20, 30, 215)
    COR_BORDA = (110, 125, 165)
    COR_TEXTO = (235, 238, 245)
    COR_DESTAQUE = (250, 215, 95)

    # 3. Game Loop a 60 FPS com delta time (sem time.sleep)
    rodando = True
    while rodando:
        dt = relogio.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_k:
                    # Aplica 1 dano de teste (respeita os i-frames de 1 segundo)
                    player.receber_dano(1)
                elif evento.key == pygame.K_h:
                    # Alterna exibição visual das hitboxes
                    exibir_hitboxes = not exibir_hitboxes
                elif evento.key == pygame.K_r:
                    # Reinicia o personagem no chão padrão para repetir os testes
                    player = Player(x=200)

        teclas = pygame.key.get_pressed()

        # Atualiza o Player usando CHAO_Y como chão padrão (sem plataformas extras)
        player.atualizar(teclas=teclas, dt=dt)

        # Renderização do fundo e do chão em CHAO_Y
        tela.fill(COR_FUNDO)
        pygame.draw.rect(tela, COR_CHAO, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
        pygame.draw.line(tela, COR_LINHA_CHAO, (0, CHAO_Y), (LARGURA, CHAO_Y), 3)

        # Desenha o Player e, se ativo, a hitbox do corpo e a hitbox de ataque
        player.desenhar(tela, depuracao=exibir_hitboxes)

        # Painel de status (topo esquerdo)
        painel_status = pygame.Surface((460, 190), pygame.SRCALPHA)
        pygame.draw.rect(painel_status, COR_PAINEL, painel_status.get_rect(), border_radius=10)
        pygame.draw.rect(painel_status, COR_BORDA, painel_status.get_rect(), 2, border_radius=10)
        tela.blit(painel_status, (20, 20))

        dados_ataque = player.obter_dados_ataque()
        orientacao = "ESQUERDA" if player.olhando_para_esquerda else "DIREITA"
        estado_invuln = "SIM (i-frames)" if player.invulneravel else "NÃO"
        estado_ataque = f"ATIVO (id #{dados_ataque['id_ataque']})" if dados_ataque["ativo"] else "INATIVO"

        linhas_status = [
            f"Vidas: {player.vida} / {player.vida_maxima} ({'VIVO' if player.esta_vivo else 'MORTO'})",
            f"Animação: {player.estado_animacao} (frame {player.indice_frame + 1})",
            f"Velocidade Horizontal: {player.velocidade_x_atual:.1f} px/s",
            f"Invulnerável: {estado_invuln}",
            f"Ataque: {estado_ataque}",
            f"Orientação: {orientacao} | No chão: {'SIM' if player.no_chao else 'NÃO'} | Rect: {player.rect.width}x{player.rect.height}",
        ]

        tela.blit(fonte_titulo.render("STATUS DO PLAYER", True, COR_DESTAQUE), (34, 30))
        for i, linha in enumerate(linhas_status):
            tela.blit(fonte_info.render(linha, True, COR_TEXTO), (34, 58 + i * 24))

        # Painel de legenda de controles (topo direito)
        painel_controles = pygame.Surface((430, 190), pygame.SRCALPHA)
        pygame.draw.rect(painel_controles, COR_PAINEL, painel_controles.get_rect(), border_radius=10)
        pygame.draw.rect(painel_controles, COR_BORDA, painel_controles.get_rect(), 2, border_radius=10)
        tela.blit(painel_controles, (LARGURA - 450, 20))

        legenda = [
            "[A / D] Mover esquerda / direita",
            "[W / ESPAÇO] Pular",
            "[S / SETA BAIXO] Agachar (CROUCH)",
            "[J / F] Atacar (hitbox vermelha)",
            "[K] Simular dano (-1 vida, i-frames 1s)",
            "[H] Hitboxes ON/OFF  |  [R] Resetar  |  [ESC] Sair",
        ]

        tela.blit(fonte_titulo.render("CONTROLES DE TESTE", True, COR_DESTAQUE), (LARGURA - 436, 30))
        for i, item in enumerate(legenda):
            tela.blit(fonte_info.render(item, True, COR_TEXTO), (LARGURA - 436, 58 + i * 24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
