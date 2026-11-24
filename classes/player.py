from pathlib import Path
import pygame


class Player:
    """
    Classe principal do personagem controlado pelo jogador no ESCAPE-FROM-CIN.

    Responsável por gerenciar:
    - Posição (coordenadas float sincronizadas com pygame.Rect) e física 2D.
    - Movimentação horizontal e vertical com separação de eixos e delta time limitado.
    - Colisões com plataformas, paredes e teto via coleção opcional de pygame.Rect.
    - Estados e alternância de animações (STOP, RUN, JUMP, CROUCH, DEAD) sem oscilações.
    - Sistema de ataque com cooldown, duração, hitbox direcional e controle de hit único.
    - Sistema de vida com proteção contra valores inválidos e bloqueio ao morrer.
    """

    def __init__(self, x=100, y=100):
        # 1. Posição e dimensões físicas
        self.x = float(x)
        self.y = float(y)
        self.largura = 60
        self.altura_normal = 140
        self.altura_agachado = 96
        self.altura = self.altura_normal
        self.rect = pygame.Rect(round(self.x), round(self.y), self.largura, self.altura)

        # 2. Física e movimentação
        self.velocidade_horizontal = 300.0  # Pixels por segundo (~5 px/frame a 60 FPS)
        self.velocidade_vertical = 0.0      # Velocidade atual no eixo Y (pixels/segundo)
        self.velocidade_x_atual = 0.0       # Velocidade atual no eixo X (pixels/segundo)
        self.gravidade = 1200.0             # Aceleração da gravidade (pixels/s²)
        self.forca_pulo = -650.0            # Impulso vertical inicial para o pulo
        self.dt_maximo = 0.05               # Limite de delta time para evitar tunelamento (20 FPS)
        self.no_chao = False                # Indica se o personagem está apoiado em superfície sólida

        # 3. Orientação e estados
        self.olhando_para_esquerda = False
        self.estado_movimento = "PARADO"    # "PARADO" ou "ANDANDO"
        self.estado_animacao = "STOP"       # "STOP", "RUN", "JUMP", "CROUCH", "DEAD"
        self.agachado = False               # Indica se o personagem está atualmente agachado
        self._intencao_agachar = False      # Indica se a tecla de agachar está pressionada
        self._intencao_movimento_x = 0      # Direção horizontal solicitada no frame (-1, 0 ou 1)

        # 4. Combate (Vida e Ataque)
        self.vida_maxima = 100
        self.vida = self.vida_maxima
        self.dano_ataque = 25
        self.atacando = False
        self.duracao_ataque_ms = 180        # Duração ativa da hitbox de ataque
        self.tempo_recarga_ataque_ms = 400  # Cooldown entre ataques
        self.ultimo_ataque_tempo = -self.tempo_recarga_ataque_ms
        self.alcance_ataque_largura = 50
        self.alcance_ataque_altura = 80
        self.hitbox_ataque = None           # Retângulo da área de dano do ataque
        self.id_ataque = 0                  # Identificador incremental único por ataque disparado
        self._alvos_atingidos_no_ataque = set()

        # 5. Carregamento dos frames de animação (independente do diretório de trabalho)
        self.animacoes = self._carregar_todas_animacoes()
        self.indice_frame = 0
        self.intervalo_animacao_ms = 120    # Tempo entre quadros da animação
        self.ultimo_tempo_animacao = pygame.time.get_ticks()

    @property
    def esta_vivo(self):
        """Retorna True se o personagem ainda possui pontos de vida positivos."""
        return self.vida > 0

    def _carregar_todas_animacoes(self):
        """
        Carrega todos os 19 sprites organizados nas 4 pastas usando pathlib.Path
        relativo à localização de classes/player.py.
        """
        raiz_projeto = Path(__file__).resolve().parent.parent
        pasta_sprites = raiz_projeto / "assets" / "player"
        display_ativo = pygame.display.get_surface() is not None

        def carregar_lista(pasta, prefixo, total):
            lista = []
            for i in range(1, total + 1):
                caminho = pasta_sprites / pasta / f"{prefixo}{i:02d}.png"
                img = pygame.image.load(str(caminho))
                if display_ativo:
                    img = img.convert_alpha()
                lista.append(img)
            return lista

        caminho_crouch = pasta_sprites / "CROUCH" / "sprite_2_03_03.png"
        img_crouch = pygame.image.load(str(caminho_crouch))
        if display_ativo:
            img_crouch = img_crouch.convert_alpha()

        return {
            "STOP": carregar_lista("STOP", "sprite_1_01_", 3),
            "RUN": carregar_lista("RUN", "sprite_2_01_", 7),
            "JUMP": carregar_lista("JUMP", "sprite_1_03_", 4),
            "CROUCH": [img_crouch],
            "DEAD": carregar_lista("FALL", "sprite_2_06_", 5),
        }

    def pode_levantar(self, plataformas=None):
        """
        Verifica se existe espaço livre acima do personagem para restaurar a altura normal
        sem atravessar tetos ou plataformas sólidas.
        """
        if not plataformas:
            return True

        rect_em_pe = pygame.Rect(
            self.rect.x,
            self.rect.bottom - self.altura_normal,
            self.largura,
            self.altura_normal,
        )
        for plat in plataformas:
            if rect_em_pe.colliderect(plat):
                return False
        return True

    def _aplicar_postura_agachado(self, agachar, plataformas=None):
        """
        Ajusta a altura do rect mantendo os pés (rect.bottom) fixos na mesma posição.
        Só permite levantar quando há espaço livre acima do personagem.
        """
        if agachar:
            if not self.agachado:
                base_y = self.rect.bottom
                self.altura = self.altura_agachado
                self.rect.height = self.altura_agachado
                self.rect.bottom = base_y
                self.y = float(self.rect.y)
                self.agachado = True
        else:
            if self.agachado and self.pode_levantar(plataformas):
                base_y = self.rect.bottom
                self.altura = self.altura_normal
                self.rect.height = self.altura_normal
                self.rect.bottom = base_y
                self.y = float(self.rect.y)
                self.agachado = False

    def processar_input(self, teclas, dt=0.0, plataformas=None):
        """
        Lê os comandos do teclado e registra a intenção de agachamento, movimento, pulo e ataque.
        Quando o personagem está sem vida, todas as entradas de ação são ignoradas.
        """
        if not self.esta_vivo:
            self._intencao_agachar = False
            self._intencao_movimento_x = 0
            self.velocidade_x_atual = 0.0
            self.estado_movimento = "PARADO"
            self.atacando = False
            self.hitbox_ataque = None
            return

        # Leitura da tecla de agachar (S ou Seta para Baixo)
        quer_agachar = bool(teclas[pygame.K_s] or teclas[pygame.K_DOWN])
        self._intencao_agachar = quer_agachar

        # Só pode agachar quando estiver apoiado no chão
        if quer_agachar and self.no_chao:
            self._aplicar_postura_agachado(True, plataformas)
        elif self.agachado:
            self._aplicar_postura_agachado(False, plataformas)

        # Enquanto agachado (inclusive preso sob um teto baixo): impede andar, pular e atacar,
        # preservando a direção atual para a qual o personagem está olhando.
        if self.agachado:
            self._intencao_movimento_x = 0
            self.velocidade_x_atual = 0.0
            self.estado_movimento = "PARADO"
            return

        # Movimentação horizontal (A / D)
        movimento_x = 0
        if teclas[pygame.K_a]:
            movimento_x -= 1
        if teclas[pygame.K_d]:
            movimento_x += 1

        self._intencao_movimento_x = movimento_x
        self.velocidade_x_atual = movimento_x * self.velocidade_horizontal

        if movimento_x < 0:
            self.olhando_para_esquerda = True
            self.estado_movimento = "ANDANDO"
        elif movimento_x > 0:
            self.olhando_para_esquerda = False
            self.estado_movimento = "ANDANDO"
        else:
            self.estado_movimento = "PARADO"

        # Pulo (W ou Barra de Espaço)
        if (teclas[pygame.K_w] or teclas[pygame.K_SPACE]) and self.no_chao:
            self.pular()

        # Ataque (J ou Tecla F)
        if teclas[pygame.K_j] or teclas[pygame.K_f]:
            self.atacar()

    def pular(self):
        """Executa o pulo caso o personagem esteja vivo, no chão e não agachado."""
        if self.esta_vivo and self.no_chao and not self.agachado:
            self.velocidade_vertical = self.forca_pulo
            self.no_chao = False

    def atacar(self):
        """
        Dispara um ataque caso o personagem esteja vivo, não agachado e o tempo de recarga
        (400 ms) já tenha decorrido. Gera um novo id_ataque e limpa o conjunto
        de alvos já atingidos.
        """
        if not self.esta_vivo or self.agachado:
            return False

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_ataque_tempo >= self.tempo_recarga_ataque_ms:
            self.atacando = True
            self.ultimo_ataque_tempo = tempo_atual
            self.id_ataque += 1
            self._alvos_atingidos_no_ataque.clear()
            return True
        return False

    def movimentar_horizontal(self, dt):
        """Aplica o deslocamento horizontal com base em dt e sincroniza rect.x."""
        self.x += self.velocidade_x_atual * dt
        self.rect.x = round(self.x)

    def resolver_colisoes_horizontais(self, plataformas, largura_tela=1280):
        """
        Resolve colisões no eixo X contra plataformas/paredes e limites horizontais.
        Deve ser chamado imediatamente após movimentar_horizontal().
        """
        if plataformas:
            for plat in plataformas:
                if self.rect.colliderect(plat):
                    if self.velocidade_x_atual > 0:
                        self.rect.right = plat.left
                        self.x = float(self.rect.x)
                    elif self.velocidade_x_atual < 0:
                        self.rect.left = plat.right
                        self.x = float(self.rect.x)

        # Limite horizontal esquerdo
        if self.rect.left < 0:
            self.rect.left = 0
            self.x = float(self.rect.x)

        # Limite horizontal direito
        if largura_tela is not None and self.rect.right > largura_tela:
            self.rect.right = largura_tela
            self.x = float(self.rect.x)

    def aplicar_fisica(self, dt):
        """Aplica gravidade contínua, deslocamento vertical e sincroniza rect.y."""
        self.velocidade_vertical += self.gravidade * dt
        self.y += self.velocidade_vertical * dt
        self.rect.y = round(self.y)

    def resolver_colisoes_verticais(self, plataformas=None, chao_provisorio=None):
        """
        Resolve colisões no eixo Y (chão e teto) após aplicar_fisica().
        Usa a direção da velocidade vertical para separar aterrissagem de impacto no teto
        sem depender de margens mágicas ou subtração de velocidade em px/s.
        """
        self.no_chao = False

        if plataformas:
            for plat in plataformas:
                if self.rect.colliderect(plat):
                    if self.velocidade_vertical > 0:
                        self.rect.bottom = plat.top
                        self.y = float(self.rect.y)
                        self.velocidade_vertical = 0.0
                        self.no_chao = True
                    elif self.velocidade_vertical < 0:
                        self.rect.top = plat.bottom
                        self.y = float(self.rect.y)
                        self.velocidade_vertical = 0.0

            # Sonda de 1 pixel abaixo dos pés para manter no_chao estável
            # quando o personagem está apenas encostado no topo da plataforma
            if not self.no_chao and self.velocidade_vertical >= 0:
                sonda_pes = self.rect.move(0, 1)
                for plat in plataformas:
                    if sonda_pes.colliderect(plat) and self.rect.bottom <= plat.top:
                        self.rect.bottom = plat.top
                        self.y = float(self.rect.y)
                        self.velocidade_vertical = 0.0
                        self.no_chao = True
                        break

        # Chão provisório opcional para testes independentes
        if chao_provisorio is not None:
            if self.rect.bottom >= chao_provisorio:
                self.rect.bottom = int(chao_provisorio)
                self.y = float(self.rect.y)
                self.velocidade_vertical = 0.0
                self.no_chao = True

    def resolver_colisoes_plataformas(self, lista_rects_chao):
        """
        Mantido por compatibilidade com chamadas externas simples:
        executa a resolução vertical de chão e teto contra lista_rects_chao.
        """
        self.resolver_colisoes_verticais(plataformas=lista_rects_chao)

    def limitar_tela(self, largura_tela=1280, altura_tela=720, chao_provisorio=None):
        """
        Mantido por compatibilidade: aplica limites horizontais e chão provisório.
        """
        self.resolver_colisoes_horizontais(plataformas=None, largura_tela=largura_tela)
        if chao_provisorio is not None:
            self.resolver_colisoes_verticais(plataformas=None, chao_provisorio=chao_provisorio)

    def sincronizar_rect(self):
        """Atualiza a posição do rect de colisão a partir das coordenadas float x e y."""
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)

    def atualizar_hitbox_ataque(self):
        """Atualiza a área de dano do ataque e encerra o estado ativo ao expirar."""
        if not self.esta_vivo:
            self.atacando = False
            self.hitbox_ataque = None
            return

        tempo_atual = pygame.time.get_ticks()
        if self.atacando:
            if tempo_atual - self.ultimo_ataque_tempo <= self.duracao_ataque_ms:
                if self.olhando_para_esquerda:
                    hitbox_x = self.rect.left - self.alcance_ataque_largura
                else:
                    hitbox_x = self.rect.right

                hitbox_y = self.rect.centery - (self.alcance_ataque_altura // 2)
                self.hitbox_ataque = pygame.Rect(
                    hitbox_x, hitbox_y, self.alcance_ataque_largura, self.alcance_ataque_altura
                )
            else:
                self.atacando = False
                self.hitbox_ataque = None
        else:
            self.hitbox_ataque = None

    def atualizar_estado_animacao(self):
        """
        Seleciona a animação correspondente com base na vida, estado físico e movimento:
        - DEAD: quando a vida chega a zero (prioridade máxima).
        - JUMP: durante toda a trajetória aérea (subida e descida).
        - CROUCH: agachado no chão.
        - RUN: andando no chão.
        - STOP: parado no chão.
        """
        if not self.esta_vivo:
            novo_estado = "DEAD"
        elif not self.no_chao:
            novo_estado = "JUMP"
        elif self.agachado:
            novo_estado = "CROUCH"
        elif self.estado_movimento == "ANDANDO":
            novo_estado = "RUN"
        else:
            novo_estado = "STOP"

        if novo_estado != self.estado_animacao:
            self.estado_animacao = novo_estado
            self.indice_frame = 0
            self.ultimo_tempo_animacao = pygame.time.get_ticks()

    def atualizar_animacao(self):
        """
        Avança os frames da animação atual com base no tempo decorrido.
        No estado DEAD, reproduz a sequência uma única vez e congela no último frame.
        """
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_tempo_animacao >= self.intervalo_animacao_ms:
            frames = self.animacoes[self.estado_animacao]
            if self.estado_animacao == "DEAD":
                if self.indice_frame < len(frames) - 1:
                    self.indice_frame += 1
            else:
                self.indice_frame = (self.indice_frame + 1) % len(frames)
            self.ultimo_tempo_animacao = tempo_atual

    def obter_dados_ataque(self):
        """
        Retorna informações para o sistema de inimigos detectar o ataque.

        Como usar no módulo de inimigos (para evitar dano repetido no mesmo golpe):
        1. Verifique se `dados["ativo"]` é True e se `inimigo.rect.colliderect(dados["hitbox"])`.
        2. Chame `player.registrar_acerto_ataque(inimigo)` (ou guarde `dados["id_ataque"]` no inimigo).
        3. Apenas aplique `dados["dano"]` se `registrar_acerto_ataque(inimigo)` retornar True.
        """
        ativo = self.esta_vivo and self.atacando and self.hitbox_ataque is not None
        return {
            "ativo": ativo,
            "hitbox": self.hitbox_ataque if ativo else None,
            "dano": self.dano_ataque,
            "id_ataque": self.id_ataque,
        }

    def registrar_acerto_ataque(self, alvo):
        """
        Registra que um alvo específico (objeto ou ID hashable) foi atingido pelo ataque atual.
        Retorna True se o acerto é inédito neste golpe (deve aplicar dano) ou False se o alvo
        já foi atingido durante o mesmo ataque ou se o ataque não está ativo.
        """
        if not (self.esta_vivo and self.atacando and self.hitbox_ataque is not None):
            return False

        chave_alvo = id(alvo) if not isinstance(alvo, (int, str)) else alvo
        if chave_alvo in self._alvos_atingidos_no_ataque:
            return False

        self._alvos_atingidos_no_ataque.add(chave_alvo)
        return True

    def receber_dano(self, quantidade):
        """
        Aplica dano ao personagem reduzindo seus pontos de vida.
        Ignora quantidades inválidas (não numéricas ou <= 0) e mantém a vida entre 0 e vida_maxima.
        Retorna True se o personagem morreu (vida == 0), False caso contrário.
        """
        if not isinstance(quantidade, (int, float)) or isinstance(quantidade, bool):
            return not self.esta_vivo

        if quantidade <= 0:
            return not self.esta_vivo

        self.vida = max(0, min(self.vida_maxima, self.vida - quantidade))
        if not self.esta_vivo:
            self._intencao_movimento_x = 0
            self.velocidade_x_atual = 0.0
            self.estado_movimento = "PARADO"
            self.atacando = False
            self.hitbox_ataque = None
        return not self.esta_vivo

    def atualizar(
        self,
        teclas,
        dt,
        largura_tela=1280,
        altura_tela=720,
        chao_provisorio=None,
        plataformas=None,
    ):
        """
        Método central de atualização do Player chamado a cada iteração do Game Loop.

        Ordem do pipeline:
        1. Limitar dt ao máximo de 0.05s.
        2. Processar entrada do jogador.
        3. Movimentar horizontalmente.
        4. Resolver colisões horizontais (paredes e limites).
        5. Aplicar gravidade e movimentar verticalmente.
        6. Resolver colisões verticais (chão e teto).
        7. Atualizar hitbox de ataque.
        8. Atualizar estado e animação.
        """
        # 1. Limitar delta time
        dt_seguro = min(max(float(dt), 0.0), self.dt_maximo)

        # 2. Processar entrada
        self.processar_input(teclas, dt_seguro, plataformas=plataformas)

        # 3. Movimentação horizontal
        self.movimentar_horizontal(dt_seguro)

        # 4. Colisões horizontais
        self.resolver_colisoes_horizontais(plataformas, largura_tela=largura_tela)

        # 5. Gravidade e movimentação vertical
        self.aplicar_fisica(dt_seguro)

        # 6. Colisões verticais
        self.resolver_colisoes_verticais(
            plataformas=plataformas,
            chao_provisorio=chao_provisorio,
        )

        # 7. Hitbox de ataque
        self.atualizar_hitbox_ataque()

        # 8. Estado e animação
        self.atualizar_estado_animacao()
        self.atualizar_animacao()

    def desenhar(self, tela, depuracao=False):
        """
        Desenha o personagem na tela com o sprite atual e alinhamento pela base do rect.
        Se depuracao=True, desenha também o rect de colisão e a hitbox de ataque.
        """
        frames = self.animacoes[self.estado_animacao]
        frame = frames[self.indice_frame % len(frames)]

        if self.olhando_para_esquerda:
            sprite_desenho = pygame.transform.flip(frame, True, False)
        else:
            sprite_desenho = frame

        pos_x_desenho = self.rect.centerx - (sprite_desenho.get_width() // 2)
        pos_y_desenho = self.rect.bottom - sprite_desenho.get_height()

        tela.blit(sprite_desenho, (pos_x_desenho, pos_y_desenho))

        if depuracao:
            # Retângulo de colisão do corpo do Player (Verde)
            pygame.draw.rect(tela, (0, 255, 0), self.rect, 2)

            # Hitbox da área ativa de ataque (Vermelho)
            if self.hitbox_ataque is not None:
                pygame.draw.rect(tela, (255, 50, 50), self.hitbox_ataque, 2)
