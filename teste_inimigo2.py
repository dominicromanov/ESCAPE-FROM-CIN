import pygame
from constants import LARGURA, ALTURA, FPS, CHAO_Y
from classes.inimigo import Drone


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Teste de Inimigo - Drone")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("consolas", 18)

    inimigo = Drone(velocidade_extra=1)

    # Player falso (mesmo tamanho do real: 60x140), controlado pelo mouse
    player_rect = pygame.Rect(350, CHAO_Y - 140, 60, 140)
    velocidade_mundo = 2
    depuracao = True
    ultimo_evento = "Nenhum"

    rodando = True
    while rodando:
        # 1. Eventos e controles de teste
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.KEYDOWN:
                # ESPAÇO: dá 25 de dano (testa barra de vida e queda)
                if evento.key == pygame.K_SPACE:
                    morreu = inimigo.receber_dano(25)
                    ultimo_evento = "Soco! Drone caiu." if morreu else f"Soco! Vida: {inimigo.vida}"

                # R: respawna um drone novo
                elif evento.key == pygame.K_r:
                    inimigo = Drone(velocidade_extra=1)
                    ultimo_evento = "Drone respawnado"

                # H: liga/desliga hitboxes
                elif evento.key == pygame.K_h:
                    depuracao = not depuracao

                # P: pausa/despausa o cenário
                elif evento.key == pygame.K_p:
                    velocidade_mundo = 0 if velocidade_mundo > 0 else 2

        # Player falso: mouse move na horizontal; segurar botão esquerdo = "pulando"
        mouse_x, _ = pygame.mouse.get_pos()
        player_rect.centerx = mouse_x
        pulando = pygame.mouse.get_pressed()[0]
        player_rect.bottom = CHAO_Y - 200 if pulando else CHAO_Y

        # 2. Lógica
        inimigo.atualizar(velocidade_mundo, alvo=player_rect)

        dados_ataque = inimigo.obter_dados_ataque()
        if dados_ataque["ativo"] and dados_ataque["hitbox"].colliderect(player_rect):
            inimigo.registrar_acerto()
            ultimo_evento = f"PLAYER ATINGIDO! (-{dados_ataque['dano']} vida)"

        if inimigo.deve_remover():
            inimigo = Drone(velocidade_extra=1)
            ultimo_evento = "Drone removido e recriado"

        # 3. Desenho
        tela.fill((30, 32, 40))
        pygame.draw.line(tela, (100, 100, 110), (0, CHAO_Y), (LARGURA, CHAO_Y), 3)

        # Linha de referência da altura padrão do voo
        pygame.draw.line(tela, (60, 80, 60), (0, Drone.ALTURA_PADRAO), (LARGURA, Drone.ALTURA_PADRAO), 1)

        pygame.draw.rect(tela, (70, 130, 230), player_rect, border_radius=4)
        inimigo.desenhar(tela, depuracao=depuracao)

        infos = [
            f"Estado: {inimigo.estado} | Frame: {inimigo.indice_frame} | Vida: {inimigo.vida}/{inimigo.VIDA_MAXIMA}",
            f"Altura (centro Y): {inimigo.rect.centery} | Padrao: {Drone.ALTURA_PADRAO}",
            f"Ultimo evento: {ultimo_evento}",
            "[MOUSE] mover player | [BOTAO ESQ] player 'pulando' | [ESPACO] dano 25 | [R] reset | [H] hitboxes | [P] pausar",
        ]
        for i, texto in enumerate(infos):
            tela.blit(fonte.render(texto, True, (230, 230, 230)), (20, 20 + i * 25))

        pygame.display.flip()
        relogio.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()