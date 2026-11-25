import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from classes.game_object import GameObject
from classes.player import Player
from constants import LARGURA, ALTURA, FPS, CHAO_Y


class TeclasMock:
    """Simula o retorno de pygame.key.get_pressed() para testes determinísticos."""

    def __init__(self, *teclas_ativas):
        self.ativas = set(teclas_ativas)

    def __getitem__(self, tecla):
        return tecla in self.ativas


class InimigoMock:
    """Alvo simples para validar detecção de acerto único por ataque."""

    def __init__(self, x, y, largura=50, altura=100, vida=100):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.vida = vida


class TestPlayerAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        cls.tela = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.dt = 1.0 / 60.0
        self.chao = pygame.Rect(0, 600, 1280, 120)

    def test_01_aterrissagem_em_plataformas(self):
        """Player deve cair sob gravidade e aterrissar exatamente no topo da plataforma."""
        player = Player(x=200, y=300)
        aterrissou = False
        for _ in range(120):
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            if player.no_chao:
                aterrissou = True
                break

        self.assertTrue(aterrissou, "Player não aterrissou na plataforma em 120 frames.")
        self.assertEqual(player.rect.bottom, self.chao.top)
        self.assertEqual(player.velocidade_vertical, 0.0)
        self.assertEqual(player.estado_animacao, "STOP")

    def test_02_permanencia_estavel_sobre_plataforma_120_frames(self):
        """Sobre uma plataforma, no_chao deve permanecer True e animação STOP por 120 frames sem oscilar."""
        player = Player(x=200, y=460)  # rect.bottom == 600 == chao.top
        estados = []
        flags_chao = []

        for _ in range(120):
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            estados.append(player.estado_animacao)
            flags_chao.append(player.no_chao)
            self.assertEqual(player.rect.bottom, self.chao.top)

        self.assertTrue(all(flags_chao), "no_chao oscilou para False enquanto parado na plataforma.")
        self.assertTrue(all(e == "STOP" for e in estados), f"Animação oscilou: {set(estados)}")

    def test_03_colisao_com_parede_lateral(self):
        """Player andando para direita ou esquerda não deve atravessar paredes laterais."""
        parede_dir = pygame.Rect(300, 400, 50, 200)
        parede_esq = pygame.Rect(100, 400, 50, 200)
        plataformas = [self.chao, parede_dir, parede_esq]

        player = Player(x=200, y=460)
        # Anda para direita contra parede_dir
        for _ in range(60):
            player.atualizar(TeclasMock(pygame.K_d), self.dt, plataformas=plataformas)
        self.assertEqual(player.rect.right, parede_dir.left)
        self.assertFalse(player.rect.colliderect(parede_dir))

        # Anda para esquerda contra parede_esq
        for _ in range(90):
            player.atualizar(TeclasMock(pygame.K_a), self.dt, plataformas=plataformas)
        self.assertEqual(player.rect.left, parede_esq.right)
        self.assertFalse(player.rect.colliderect(parede_esq))

    def test_04_colisao_com_teto(self):
        """Ao pular contra um teto baixo, a subida deve ser interrompida sem atravessar."""
        teto = pygame.Rect(100, 380, 300, 40)  # bottom = 420
        plataformas = [self.chao, teto]
        player = Player(x=200, y=460)  # top = 460, espaço de 40px até o teto

        player.atualizar(TeclasMock(), self.dt, plataformas=plataformas)
        self.assertTrue(player.no_chao)

        # Executa pulo com velocidade alta (-650 px/s) e simula alguns frames inclusive com dt=0.04s
        player.atualizar(TeclasMock(pygame.K_w), self.dt, plataformas=plataformas)
        bateu_teto = False
        for _ in range(20):
            player.atualizar(TeclasMock(), 0.04, plataformas=plataformas)
            self.assertGreaterEqual(player.rect.top, teto.bottom, "Player atravessou o teto!")
            if player.rect.top == teto.bottom and player.velocidade_vertical == 0.0:
                bateu_teto = True
                break

        self.assertTrue(bateu_teto, "Player não colidiu corretamente com o teto.")

    def test_05_colisao_lateral_sem_falsa_aterrissagem(self):
        """Encostar na lateral de uma plataforma caindo NÃO pode teleportar o player para o topo."""
        plataforma_flutuante = pygame.Rect(300, 500, 120, 40)
        player = Player(x=235, y=420)  # rect.right = 295, rect.bottom = 560 (abaixo do topo 500)
        player.velocidade_vertical = 250.0  # caindo rápido

        # Move para direita (D) enquanto cai encostando na lateral da plataforma
        player.atualizar(TeclasMock(pygame.K_d), self.dt, plataformas=[plataforma_flutuante])

        self.assertEqual(player.rect.right, plataforma_flutuante.left)
        self.assertNotEqual(
            player.rect.bottom,
            plataforma_flutuante.top,
            "Falsa aterrissagem: player foi teleportado para o topo ao encostar na lateral!",
        )
        self.assertFalse(player.no_chao)

    def test_06_pulo_e_retorno_ao_chao(self):
        """Pulo completo deve manter JUMP na subida e descida (nunca DEAD), impedir pulo duplo e voltar para STOP."""
        player = Player(x=200, y=460)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        self.assertTrue(player.no_chao)

        # Dispara pulo
        player.atualizar(TeclasMock(pygame.K_SPACE), self.dt, plataformas=[self.chao])
        self.assertFalse(player.no_chao)
        self.assertEqual(player.estado_animacao, "JUMP")
        vel_apos_pulo = player.velocidade_vertical

        # Tentar pular novamente no ar não pode resetar a velocidade vertical
        player.pular()
        self.assertEqual(player.velocidade_vertical, vel_apos_pulo)

        viu_subida = False
        viu_descida = False
        voltou_chao = False

        for _ in range(120):
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            self.assertNotEqual(player.estado_animacao, "DEAD", "Pulo normal nunca deve reproduzir DEAD!")
            if not player.no_chao:
                self.assertEqual(player.estado_animacao, "JUMP")
                if player.velocidade_vertical < 0:
                    viu_subida = True
                elif player.velocidade_vertical > 0:
                    viu_descida = True
            elif viu_descida:
                voltou_chao = True
                break

        self.assertTrue(viu_subida, "Não passou pela fase de subida do pulo.")
        self.assertTrue(viu_descida, "Não passou pela fase de descida do pulo com JUMP.")
        self.assertTrue(voltou_chao, "Player não retornou ao chão.")
        self.assertEqual(player.estado_animacao, "STOP")

    def test_07_queda_ao_sair_da_borda_de_plataforma(self):
        """Ao caminhar para fora de uma plataforma suspensa, deve perder no_chao e cair usando JUMP (não DEAD)."""
        plataforma_curta = pygame.Rect(100, 500, 120, 30)  # vai de X=100 até X=220
        player = Player(x=160, y=360)  # rect.bottom = 500
        player.atualizar(TeclasMock(), self.dt, plataformas=[plataforma_curta])
        self.assertTrue(player.no_chao)

        saiu_e_caiu = False
        for _ in range(60):
            player.atualizar(TeclasMock(pygame.K_d), self.dt, plataformas=[plataforma_curta])
            if player.rect.left >= plataforma_curta.right:
                self.assertFalse(player.no_chao, "no_chao continuou True após sair da borda.")
                self.assertEqual(player.estado_animacao, "JUMP")
                self.assertGreater(player.y, 360.0)
                saiu_e_caiu = True
                break

        self.assertTrue(saiu_e_caiu, "Player não saiu da borda da plataforma.")

    def test_08_ataque_sem_dano_repetido_no_mesmo_alvo(self):
        """Um único ataque (durante seus 180ms) deve causar dano apenas uma vez no mesmo alvo."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200, y=460)
            inimigo = InimigoMock(x=265, y=480)  # dentro do alcance à direita (rect.right=260..310)

            # Inicia ataque no t=1000
            player.atualizar(TeclasMock(pygame.K_j), self.dt, plataformas=[self.chao])
            id_primeiro = player.obter_dados_ataque()["id_ataque"]
            self.assertGreater(id_primeiro, 0)

            acertos = 0
            # Simula 10 frames dentro dos 180ms ativos (t=1000..1150)
            for passo in range(10):
                tempo_simulado = 1000 + passo * 16
                player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
                dados = player.obter_dados_ataque()
                if dados["ativo"] and dados["hitbox"].colliderect(inimigo.rect):
                    if player.registrar_acerto_ataque(inimigo):
                        inimigo.vida -= dados["dano"]
                        acertos += 1

            self.assertEqual(acertos, 1, f"O mesmo ataque acertou {acertos} vezes o mesmo alvo.")
            self.assertEqual(inimigo.vida, 75)

            # Verifica expiração após 180ms (t=1200)
            tempo_simulado = 1200
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            self.assertFalse(player.obter_dados_ataque()["ativo"])

            # Verifica bloqueio de cooldown antes de 400ms (t=1350)
            tempo_simulado = 1350
            player.atualizar(TeclasMock(pygame.K_j), self.dt, plataformas=[self.chao])
            self.assertFalse(player.obter_dados_ataque()["ativo"])

            # Verifica novo ataque após 400ms (t=1400) com novo id_ataque
            tempo_simulado = 1400
            player.atualizar(TeclasMock(pygame.K_j), self.dt, plataformas=[self.chao])
            dados_segundo = player.obter_dados_ataque()
            self.assertTrue(dados_segundo["ativo"])
            self.assertEqual(dados_segundo["id_ataque"], id_primeiro + 1)
            self.assertTrue(player.registrar_acerto_ataque(inimigo))

    def test_09_ataque_contra_alvos_diferentes(self):
        """Um mesmo ataque deve poder atingir dois inimigos diferentes, mas cada um apenas uma vez."""
        tempo_simulado = 2000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200, y=460)
            inimigo_a = InimigoMock(x=265, y=480)
            inimigo_b = InimigoMock(x=280, y=490)

            player.atualizar(TeclasMock(pygame.K_f), self.dt, plataformas=[self.chao])
            dados = player.obter_dados_ataque()
            self.assertTrue(dados["ativo"])

            # Primeiro frame: ambos devem ser atingidos
            self.assertTrue(dados["hitbox"].colliderect(inimigo_a.rect))
            self.assertTrue(dados["hitbox"].colliderect(inimigo_b.rect))
            self.assertTrue(player.registrar_acerto_ataque(inimigo_a))
            self.assertTrue(player.registrar_acerto_ataque(inimigo_b))

            # Segundo frame do mesmo ataque: nenhum dos dois pode ser atingido novamente
            tempo_simulado = 2032
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            self.assertFalse(player.registrar_acerto_ataque(inimigo_a))
            self.assertFalse(player.registrar_acerto_ataque(inimigo_b))

    def test_10_dano_negativo_e_vida_maxima(self):
        """receber_dano() não pode aceitar valores negativos/inválidos nem exceder 3 vidas ou cair abaixo de 0."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200, y=460)
            self.assertEqual(player.vida_maxima, 3)
            self.assertEqual(player.vida, 3)

            player.receber_dano(-50)
            self.assertEqual(player.vida, 3)

            player.receber_dano(0)
            self.assertEqual(player.vida, 3)

            player.receber_dano("invalido")
            self.assertEqual(player.vida, 3)

            player.receber_dano(True)
            self.assertEqual(player.vida, 3)

            # Cada dano válido remove exatamente 1 vida
            morreu = player.receber_dano(1)
            self.assertFalse(morreu)
            self.assertEqual(player.vida, 2)

            player.receber_dano(-10)
            self.assertEqual(player.vida, 2)

            # Aguarda expirar i-frames para receber o 2º e 3º danos
            tempo_simulado += player.duracao_invulnerabilidade_ms
            self.assertFalse(player.receber_dano(999))
            self.assertEqual(player.vida, 1)

            tempo_simulado += player.duracao_invulnerabilidade_ms
            morreu = player.receber_dano(1)
            self.assertTrue(morreu)
            self.assertEqual(player.vida, 0)
            self.assertFalse(player.esta_vivo)

            # Dano extra após morrer não deixa vida negativa
            tempo_simulado += player.duracao_invulnerabilidade_ms
            player.receber_dano(1)
            self.assertEqual(player.vida, 0)

    def test_11_bloqueio_de_acoes_com_vida_zero(self):
        """Com vida == 0, o personagem não pode andar, pular nem atacar."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200, y=460)
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            for _ in range(3):
                player.receber_dano(1)
                tempo_simulado += player.duracao_invulnerabilidade_ms
            self.assertFalse(player.esta_vivo)

            x_inicial = player.x
            player.atualizar(
                TeclasMock(pygame.K_d, pygame.K_w, pygame.K_SPACE, pygame.K_j, pygame.K_f),
                self.dt,
                plataformas=[self.chao],
            )

            self.assertEqual(player.x, x_inicial)
            self.assertEqual(player.estado_movimento, "PARADO")
            self.assertTrue(player.no_chao)
            self.assertEqual(player.velocidade_vertical, 0.0)
            self.assertFalse(player.atacando)
            self.assertFalse(player.obter_dados_ataque()["ativo"])

    def test_12_comportamento_com_dt_elevado(self):
        """dt elevado (ex: 1.0s de travamento de janela) deve ser limitado a 0.05s."""
        player = Player(x=200, y=460)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])

        x_antes = player.x
        player.atualizar(TeclasMock(pygame.K_d), 1.0, plataformas=[self.chao])
        deslocamento_esperado = player.velocidade_horizontal * 0.05  # 300 * 0.05 = 15px

        self.assertAlmostEqual(player.x - x_antes, deslocamento_esperado, places=4)

    def test_13_carregamento_sprites_fora_da_raiz_do_projeto(self):
        """Sprites devem carregar normalmente mesmo com o diretório atual fora da raiz do projeto."""
        cwd_original = os.getcwd()
        pasta_externa = Path(cwd_original) / "classes"
        try:
            os.chdir(pasta_externa)
            player = Player(x=100, y=100)
            total_sprites = sum(len(frames) for frames in player.animacoes.values())
            self.assertEqual(len(player.animacoes["STOP"]), 3)
            self.assertEqual(len(player.animacoes["RUN"]), 7)
            self.assertEqual(len(player.animacoes["JUMP"]), 4)
            self.assertEqual(len(player.animacoes["CROUCH"]), 1)
            self.assertEqual(len(player.animacoes["ATTACK"]), 8)
            self.assertEqual(len(player.animacoes["DEAD"]), 5)
            self.assertEqual(total_sprites, 28)
        finally:
            os.chdir(cwd_original)

    def test_14_animacao_morte_completa_sem_reiniciar(self):
        """Ao chegar a vida 0, reproduz DEAD uma única vez (frames 0..4) e congela no último frame."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200, y=460)
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            self.assertEqual(player.estado_animacao, "STOP")

            # Zera as 3 vidas do jogador respeitando i-frames
            self.assertFalse(player.receber_dano(1))
            tempo_simulado += player.duracao_invulnerabilidade_ms
            self.assertFalse(player.receber_dano(1))
            tempo_simulado += player.duracao_invulnerabilidade_ms
            morreu = player.receber_dano(1)
            self.assertTrue(morreu)
            self.assertFalse(player.esta_vivo)

            # Primeira atualização após morrer: entra em DEAD no frame 0
            tempo_simulado += 16
            tempo_inicio_morte = tempo_simulado
            player.atualizar(
                TeclasMock(pygame.K_d, pygame.K_w, pygame.K_j),
                self.dt,
                plataformas=[self.chao],
            )
            self.assertEqual(player.estado_animacao, "DEAD")
            self.assertEqual(player.indice_frame, 0)

            frames_vistos = [player.indice_frame]
            # Avança o tempo em passos de 120ms por 10 ciclos (muito além dos 5 frames)
            for passo in range(1, 11):
                tempo_simulado = tempo_inicio_morte + passo * 120
                player.atualizar(
                    TeclasMock(pygame.K_a, pygame.K_SPACE, pygame.K_f),
                    self.dt,
                    plataformas=[self.chao],
                )
                self.assertEqual(player.estado_animacao, "DEAD")
                frames_vistos.append(player.indice_frame)

            # Deve percorrer 0, 1, 2, 3, 4 e permanecer em 4 sem reiniciar para 0
            self.assertEqual(frames_vistos, [0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4])

    def test_15_agachar_permanecer_e_levantar(self):
        """Agachar com S ou SETA BAIXO mantém CROUCH, pés alinhados, direção preservada e retorna ao soltar."""
        player = Player(x=200, y=460)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        self.assertTrue(player.no_chao)

        # Olha para a esquerda antes de agachar
        player.atualizar(TeclasMock(pygame.K_a), self.dt, plataformas=[self.chao])
        self.assertTrue(player.olhando_para_esquerda)
        base_antes = player.rect.bottom

        # Agacha com S e permanece por 30 frames
        for _ in range(30):
            player.atualizar(TeclasMock(pygame.K_s), self.dt, plataformas=[self.chao])
            self.assertTrue(player.agachado)
            self.assertEqual(player.estado_animacao, "CROUCH")
            self.assertEqual(player.rect.height, player.altura_agachado)
            self.assertEqual(player.rect.bottom, base_antes)
            self.assertTrue(player.olhando_para_esquerda)

        # Solta S parado -> volta para STOP e restaura altura mantendo os pés alinhados
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        self.assertFalse(player.agachado)
        self.assertEqual(player.estado_animacao, "STOP")
        self.assertEqual(player.rect.height, player.altura_normal)
        self.assertEqual(player.rect.bottom, base_antes)

        # Agacha com SETA PARA BAIXO e ao soltar já andando com D -> volta para RUN
        player.atualizar(TeclasMock(pygame.K_DOWN), self.dt, plataformas=[self.chao])
        self.assertEqual(player.estado_animacao, "CROUCH")
        player.atualizar(TeclasMock(pygame.K_d), self.dt, plataformas=[self.chao])
        self.assertFalse(player.agachado)
        self.assertEqual(player.estado_animacao, "RUN")

    def test_16_agachado_impede_movimento_pulo_e_ataque(self):
        """Enquanto agachado, não pode andar, pular nem atacar."""
        player = Player(x=200, y=460)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        x_inicial = player.x

        player.atualizar(
            TeclasMock(pygame.K_s, pygame.K_d, pygame.K_w, pygame.K_SPACE, pygame.K_j, pygame.K_f),
            self.dt,
            plataformas=[self.chao],
        )

        self.assertTrue(player.agachado)
        self.assertEqual(player.estado_animacao, "CROUCH")
        self.assertEqual(player.x, x_inicial)
        self.assertTrue(player.no_chao)
        self.assertEqual(player.velocidade_vertical, 0.0)
        self.assertFalse(player.atacando)
        self.assertFalse(player.obter_dados_ataque()["ativo"])

    def test_17_nao_agachar_no_ar_nem_morto(self):
        """Não pode entrar em CROUCH durante pulo/queda nem após morrer."""
        player = Player(x=200, y=460)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])

        # Pula e segura S no ar
        player.atualizar(TeclasMock(pygame.K_w), self.dt, plataformas=[self.chao])
        self.assertFalse(player.no_chao)
        player.atualizar(TeclasMock(pygame.K_s), self.dt, plataformas=[self.chao])
        self.assertFalse(player.agachado)
        self.assertEqual(player.estado_animacao, "JUMP")
        self.assertEqual(player.rect.height, player.altura_normal)

        # Volta ao chão e morre -> segurar S não pode trocar DEAD para CROUCH
        for _ in range(120):
            player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
            if player.no_chao:
                break
        tempo_simulado = 5000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            for _ in range(3):
                player.receber_dano(1)
                tempo_simulado += player.duracao_invulnerabilidade_ms
            player.atualizar(TeclasMock(pygame.K_s), self.dt, plataformas=[self.chao])
            self.assertFalse(player.agachado)
            self.assertEqual(player.estado_animacao, "DEAD")

    def test_18_nao_atravessar_teto_ao_levantar(self):
        """Se houver um obstáculo acima impedindo a altura normal, o player permanece agachado."""
        player = Player(x=200, y=460)  # pés em 600, altura normal 140 (topo 460), agachado 96 (topo 504)
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])

        # Agacha em área livre
        player.atualizar(TeclasMock(pygame.K_s), self.dt, plataformas=[self.chao])
        self.assertTrue(player.agachado)
        self.assertEqual(player.rect.top, 504)
        self.assertEqual(player.rect.bottom, 600)

        # Obstáculo baixo posicionado entre Y=470 e Y=500 (acima da cabeça agachado, mas bloqueia ficar em pé)
        teto_baixo = pygame.Rect(150, 470, 200, 30)
        plataformas = [self.chao, teto_baixo]

        # Solta S sob o teto baixo: deve continuar agachado sem colidir/atravessar o teto
        player.atualizar(TeclasMock(), self.dt, plataformas=plataformas)
        self.assertTrue(player.agachado, "Player levantou mesmo com teto baixo acima da cabeça!")
        self.assertEqual(player.estado_animacao, "CROUCH")
        self.assertEqual(player.rect.height, player.altura_agachado)
        self.assertEqual(player.rect.bottom, 600)
        self.assertFalse(player.rect.colliderect(teto_baixo))

        # Sem o teto baixo acima, ao soltar S deve levantar normalmente
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        self.assertFalse(player.agachado)
        self.assertEqual(player.estado_animacao, "STOP")
        self.assertEqual(player.rect.height, player.altura_normal)
        self.assertEqual(player.rect.bottom, 600)

    def test_19_heranca_game_object_imagem_e_hitbox(self):
        """Player deve herdar de GameObject, preservar hitbox 60x140/60x96 e sincronizar self.imagem."""
        player = Player(x=200, y=460)
        self.assertIsInstance(player, GameObject)
        self.assertEqual(player.rect.size, (60, 140))
        self.assertIs(player.imagem, player.animacoes["STOP"][0])

        # Ao agachar, hitbox muda para 60x96 e self.imagem acompanha CROUCH
        player.atualizar(TeclasMock(), self.dt, plataformas=[self.chao])
        player.atualizar(TeclasMock(pygame.K_s), self.dt, plataformas=[self.chao])
        self.assertEqual(player.rect.size, (60, 96))
        self.assertIs(player.imagem, player.animacoes["CROUCH"][0])

        # Ao andar para a esquerda, self.imagem reflete o sprite espelhado de RUN
        player.atualizar(TeclasMock(pygame.K_a), self.dt, plataformas=[self.chao])
        self.assertEqual(player.rect.size, (60, 140))
        self.assertEqual(player.estado_animacao, "RUN")
        self.assertEqual(player.imagem.get_size(), player.animacoes["RUN"][0].get_size())
        self.assertIsNot(player.imagem, player.animacoes["RUN"][0])

    def test_20_chao_padrao_chao_y_sem_plataformas(self):
        """Sem plataformas nem chao_provisorio, Player deve reconhecer CHAO_Y como chão padrão."""
        player = Player(x=200, y=300)
        for _ in range(120):
            player.atualizar(TeclasMock(), self.dt)
            if player.no_chao:
                break

        self.assertTrue(player.no_chao)
        self.assertEqual(player.rect.bottom, CHAO_Y)
        self.assertEqual(player.estado_animacao, "STOP")

        # Também funciona chamando atualizar() sem argumentos opcionais (teclas e dt padrão)
        player_padrao = Player(x=150)
        self.assertEqual(player_padrao.rect.bottom, CHAO_Y)
        player_padrao.atualizar()
        self.assertTrue(player_padrao.no_chao)
        self.assertEqual(player_padrao.rect.bottom, CHAO_Y)

    def test_21_sistema_tres_vidas_e_invulnerabilidade_temporaria(self):
        """Após sofrer dano, i-frames impedem perda de múltiplas vidas em frames consecutivos."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200)
            self.assertEqual(player.vida, 3)
            self.assertFalse(player.invulneravel)

            # 1º contato com inimigo: perde 1 vida e entra em invulnerabilidade
            morreu = player.receber_dano(1)
            self.assertFalse(morreu)
            self.assertEqual(player.vida, 2)
            self.assertTrue(player.invulneravel)

            # 30 frames consecutivos de colisão (~480ms < 1000ms): não perde mais vidas
            for frame in range(1, 31):
                tempo_simulado = 1000 + frame * 16
                self.assertTrue(player.invulneravel)
                self.assertFalse(player.receber_dano(1))
            self.assertEqual(player.vida, 2)

            # Após expirar a invulnerabilidade (t=2000ms): novo contato remove a 2ª vida
            tempo_simulado = 2000
            self.assertFalse(player.invulneravel)
            self.assertFalse(player.receber_dano(1))
            self.assertEqual(player.vida, 1)
            self.assertTrue(player.invulneravel)

            # Novo contato após nova janela (t=3000ms): remove a 3ª vida e morre
            tempo_simulado = 3000
            self.assertTrue(player.receber_dano(1))
            self.assertEqual(player.vida, 0)
            self.assertFalse(player.esta_vivo)
            self.assertFalse(player.invulneravel)

    def test_22_animacao_ataque_progressao_e_retorno(self):
        """Ataque deve carregar 8 frames, progredir 0..7 em ordem e retornar ao estado atual (STOP/RUN)."""
        tempo_simulado = 1000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200)
            self.assertEqual(len(player.animacoes["ATTACK"]), 8)
            player.atualizar(TeclasMock(), self.dt)
            self.assertEqual(player.estado_animacao, "STOP")

            # Inicia ataque com J em t=1000
            player.atualizar(TeclasMock(pygame.K_j), self.dt)
            self.assertTrue(player.animando_ataque)
            self.assertEqual(player.estado_animacao, "ATTACK")
            self.assertEqual(player.indice_frame, 0)

            frames_vistos = [player.indice_frame]
            # Avança 7 intervalos de 45 ms -> percorre frames 1..7
            for passo in range(1, 8):
                tempo_simulado = 1000 + passo * player.intervalo_animacao_ataque_ms
                player.atualizar(TeclasMock(), self.dt)
                self.assertEqual(player.estado_animacao, "ATTACK")
                frames_vistos.append(player.indice_frame)

            self.assertEqual(frames_vistos, [0, 1, 2, 3, 4, 5, 6, 7])

            # Próximo intervalo (t = 1000 + 8 * 45 = 1360 ms): termina animação e volta para STOP
            tempo_simulado = 1000 + 8 * player.intervalo_animacao_ataque_ms
            player.atualizar(TeclasMock(), self.dt)
            self.assertFalse(player.animando_ataque)
            self.assertEqual(player.estado_animacao, "STOP")

            # Novo ataque após cooldown (t = 1450 ms) enquanto corre -> ao terminar volta para RUN
            tempo_simulado = 1450
            player.atualizar(TeclasMock(pygame.K_d, pygame.K_f), self.dt)
            self.assertEqual(player.estado_animacao, "ATTACK")
            for passo in range(1, 9):
                tempo_simulado = 1450 + passo * player.intervalo_animacao_ataque_ms
                player.atualizar(TeclasMock(pygame.K_d), self.dt)
            self.assertFalse(player.animando_ataque)
            self.assertEqual(player.estado_animacao, "RUN")

    def test_23_animacao_ataque_orientacao_hitbox_e_cooldown(self):
        """Ataque deve espelhar self.imagem para a esquerda, manter hitbox de 180ms e respeitar cooldown de 400ms."""
        tempo_simulado = 2000
        with patch("pygame.time.get_ticks", side_effect=lambda: tempo_simulado):
            player = Player(x=200)
            player.atualizar(TeclasMock(), self.dt)

            # Ataque olhando para a direita
            player.atualizar(TeclasMock(pygame.K_j), self.dt)
            self.assertFalse(player.olhando_para_esquerda)
            self.assertIs(player.imagem, player.animacoes["ATTACK"][0])
            dados_dir = player.obter_dados_ataque()
            self.assertTrue(dados_dir["ativo"])
            self.assertEqual(dados_dir["hitbox"].left, player.rect.right)

            # Em t=2200ms (200ms > 180ms): hitbox já encerrou, mas animação visual ATTACK ainda continua!
            tempo_simulado = 2200
            player.atualizar(TeclasMock(), self.dt)
            self.assertFalse(player.obter_dados_ataque()["ativo"])
            self.assertTrue(player.animando_ataque)
            self.assertEqual(player.estado_animacao, "ATTACK")

            # Em t=2350ms (350ms < 400ms cooldown): pressionar J não inicia novo ataque
            id_anterior = player.id_ataque
            tempo_simulado = 2350
            player.atualizar(TeclasMock(pygame.K_j), self.dt)
            self.assertEqual(player.id_ataque, id_anterior)

            # Em t=2500ms (>= 400ms cooldown): vira para a esquerda e ataca
            tempo_simulado = 2500
            player.atualizar(TeclasMock(pygame.K_a, pygame.K_f), self.dt)
            self.assertTrue(player.olhando_para_esquerda)
            self.assertEqual(player.estado_animacao, "ATTACK")
            self.assertEqual(player.id_ataque, id_anterior + 1)
            # self.imagem deve ser versão espelhada (nova Surface com mesmo tamanho)
            self.assertIsNot(player.imagem, player.animacoes["ATTACK"][0])
            self.assertEqual(player.imagem.get_size(), player.animacoes["ATTACK"][0].get_size())
            dados_esq = player.obter_dados_ataque()
            self.assertTrue(dados_esq["ativo"])
            self.assertEqual(dados_esq["hitbox"].right, player.rect.left)


if __name__ == "__main__":
    unittest.main(verbosity=2)
