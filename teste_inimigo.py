import pygame
from constants import LARGURA, ALTURA, FPS, CHAO_Y
from classes.inimigo import Aspirador


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Teste de Inimigo - Aspirador")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("consolas", 18)

    # Cria o primeiro inimigo
    inimigo = Aspirador(velocidade_extra=1)

    # Simula um player simples para testar a detecção e o ataque
    player_rect = pygame.Rect(350, CHAO_Y - 80, 40, 80)
    velocidade_mundo = 2
    depuracao = True
    ultimo_evento = "Nenhum"

    rodando = True
    while rodando:
        # 1. Eventos e Controles de Teste
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.KEYDOWN:
                # ESPAÇO: Dá 25 de dano no inimigo (testa barra de vida e morte)
                if evento.key == pygame.K_SPACE:
                    morreu = inimigo.receber_dano(25)
                    ultimo_evento = "Soco! Inimigo morreu." if morreu else f"Soco! Vida: {inimigo.vida}"

                # R: Respawna um novo inimigo na direita
                elif evento.key == pygame.K_r:
                    inimigo = Aspirador(velocidade_extra=1)
                    ultimo_evento = "Inimigo respawnado"

                # D: Liga/desliga as hitboxes (retângulos verde e vermelho)
                elif evento.key == pygame.K_d:
                    depuracao = not depuracao

                # P: Pausa/despausa o movimento do cenário
                elif evento.key == pygame.K_p:
                    velocidade_mundo = 0 if velocidade_mundo > 0 else 2

        # Move o player falso com o mouse (horizontalmente) para testar aproximação
        mouse_x, _ = pygame.mouse.get_pos()
        player_rect.centerx = mouse_x

        # 2. Atualização da Lógica
        inimigo.atualizar(velocidade_mundo, alvo=player_rect)

        # Verifica se o ataque do inimigo acertou o player falso
        dados_ataque = inimigo.obter_dados_ataque()
        if dados_ataque["ativo"] and dados_ataque["hitbox"].colliderect(player_rect):
            inimigo.registrar_acerto()
            ultimo_evento = f"PLAYER ATINGIDO! (-{dados_ataque['dano']} vida)"

        # Se saiu da tela ou terminou a animação de morte, cria outro automaticamente
        if inimigo.deve_remover():
            inimigo = Aspirador(velocidade_extra=1)
            ultimo_evento = "Inimigo removido e recriado"

        # 3. Desenho na Tela
        tela.fill((30, 32, 40))  # Fundo escuro

        # Linha do chão
        pygame.draw.line(tela, (100, 100, 110), (0, CHAO_Y), (LARGURA, CHAO_Y), 3)

        # Desenha o Player falso (azul)
        pygame.draw.rect(tela, (70, 130, 230), player_rect, border_radius=4)

        # Desenha o Aspirador (passando depuracao=True para ver hitboxes)
        inimigo.desenhar(tela, depuracao=depuracao)

        # Painel de informações no topo
        infos = [
            f"Estado: {inimigo.estado} | Frame: {inimigo.indice_frame} | Vida: {inimigo.vida}/{inimigo.VIDA_MAXIMA}",
            f"Ultimo evento: {ultimo_evento}",
            "Controles: [MOUSE] Mover Player | [ESPACO] Dar Dano (25) | [R] Resetar | [D] Hitboxes | [P] Pausar Chão"
        ]
        for i, texto in enumerate(infos):
            superficie_texto = fonte.render(texto, True, (230, 230, 230))
            tela.blit(superficie_texto, (20, 20 + i * 25))

        pygame.display.flip()
        relogio.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()