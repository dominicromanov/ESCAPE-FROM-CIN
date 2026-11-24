import pygame

from classes.game_object import GameObject
from .player_animation import PlayerAnimation
from .player_combat import PlayerCombat
from .player_physics import PlayerPhysics
from constants import LARGURA, ALTURA, FPS


def _delegar_atributo(componente_nome, atributo_nome):
    """Cria uma property que lê e grava diretamente no componente dono do atributo."""
    def getter(self):
        return getattr(getattr(self, componente_nome), atributo_nome)

    def setter(self, valor):
        setattr(getattr(self, componente_nome), atributo_nome, valor)

    return property(getter, setter)


class Player(GameObject):
    """
    Classe principal do personagem controlado pelo jogador no ESCAPE-FROM-CIN.

    Herda de GameObject (padrão da equipe) e coordena três componentes internos:
    - `self.animacao` (`PlayerAnimation`): sprites (28 PNGs), estados, frames e espelhamento.
    - `self.fisica` (`PlayerPhysics`): movimento, gravidade, pulo, agachamento e colisões.
    - `self.combate` (`PlayerCombat`): 3 vidas, i-frames, ataque, cooldown e hitbox de dano.

    Preserva integralmente a API pública e os atributos acessados pelo restante do jogo.
    """

    # --- Propriedades delegadas para PlayerPhysics ---
    x = _delegar_atributo("fisica", "x")
    y = _delegar_atributo("fisica", "y")
    largura = _delegar_atributo("fisica", "largura")
    altura_normal = _delegar_atributo("fisica", "altura_normal")
    altura_agachado = _delegar_atributo("fisica", "altura_agachado")
    altura = _delegar_atributo("fisica", "altura")
    velocidade_horizontal = _delegar_atributo("fisica", "velocidade_horizontal")
    velocidade_vertical = _delegar_atributo("fisica", "velocidade_vertical")
    velocidade_x_atual = _delegar_atributo("fisica", "velocidade_x_atual")
    gravidade = _delegar_atributo("fisica", "gravidade")
    forca_pulo = _delegar_atributo("fisica", "forca_pulo")
    dt_maximo = _delegar_atributo("fisica", "dt_maximo")
    no_chao = _delegar_atributo("fisica", "no_chao")
    olhando_para_esquerda = _delegar_atributo("fisica", "olhando_para_esquerda")
    estado_movimento = _delegar_atributo("fisica", "estado_movimento")
    agachado = _delegar_atributo("fisica", "agachado")
    _intencao_agachar = _delegar_atributo("fisica", "_intencao_agachar")
    _intencao_movimento_x = _delegar_atributo("fisica", "_intencao_movimento_x")

    # --- Propriedades delegadas para PlayerAnimation ---
    animacoes = _delegar_atributo("animacao", "animacoes")
    estado_animacao = _delegar_atributo("animacao", "estado_animacao")
    indice_frame = _delegar_atributo("animacao", "indice_frame")
    intervalo_animacao_ms = _delegar_atributo("animacao", "intervalo_animacao_ms")
    intervalo_animacao_ataque_ms = _delegar_atributo("animacao", "intervalo_animacao_ataque_ms")
    ultimo_tempo_animacao = _delegar_atributo("animacao", "ultimo_tempo_animacao")
    animando_ataque = _delegar_atributo("animacao", "animando_ataque")

    # --- Propriedades delegadas para PlayerCombat ---
    vida_maxima = _delegar_atributo("combate", "vida_maxima")
    vida = _delegar_atributo("combate", "vida")
    duracao_invulnerabilidade_ms = _delegar_atributo("combate", "duracao_invulnerabilidade_ms")
    ultimo_dano_tempo = _delegar_atributo("combate", "ultimo_dano_tempo")
    dano_ataque = _delegar_atributo("combate", "dano_ataque")
    atacando = _delegar_atributo("combate", "atacando")
    duracao_ataque_ms = _delegar_atributo("combate", "duracao_ataque_ms")
    tempo_recarga_ataque_ms = _delegar_atributo("combate", "tempo_recarga_ataque_ms")
    ultimo_ataque_tempo = _delegar_atributo("combate", "ultimo_ataque_tempo")
    alcance_ataque_largura = _delegar_atributo("combate", "alcance_ataque_largura")
    alcance_ataque_altura = _delegar_atributo("combate", "alcance_ataque_altura")
    hitbox_ataque = _delegar_atributo("combate", "hitbox_ataque")
    id_ataque = _delegar_atributo("combate", "id_ataque")
    _alvos_atingidos_no_ataque = _delegar_atributo("combate", "_alvos_atingidos_no_ataque")

    def __init__(self, x=100, y=None):
        self.animacao = PlayerAnimation()
        self.fisica = PlayerPhysics(x=x, y=y)
        self.combate = PlayerCombat()

        # Inicializa GameObject com o primeiro frame de STOP e vincula a hitbox física calibrada
        super().__init__(self.animacao.animacoes["STOP"][0])
        self.rect = self.fisica.rect
        self._atualizar_imagem_atual()

    @property
    def esta_vivo(self):
        """Retorna True se o personagem ainda possui pontos de vida positivos."""
        return self.combate.esta_vivo

    @property
    def invulneravel(self):
        """Retorna True enquanto o personagem estiver na janela de invulnerabilidade (i-frames)."""
        return self.combate.invulneravel

    def _atualizar_imagem_atual(self):
        """Mantém self.imagem (herdada de GameObject) sincronizada com frame e orientação atuais."""
        self.imagem = self.animacao.obter_imagem_atual(self.fisica.olhando_para_esquerda)

    def pode_levantar(self, plataformas=None):
        """Verifica se há espaço livre acima do personagem para levantar."""
        return self.fisica.pode_levantar(plataformas)

    def _aplicar_postura_agachado(self, agachar, plataformas=None):
        """Ajusta a altura do rect mantendo os pés (rect.bottom) fixos."""
        self.fisica.aplicar_postura_agachado(agachar, plataformas)

    def processar_input(self, teclas, dt=0.0, plataformas=None):
        """
        Lê os comandos do teclado e coordena agachamento, movimento, pulo e ataque.
        Quando o personagem está sem vida, todas as entradas de ação são ignoradas.
        """
        if not self.esta_vivo:
            self.fisica.parar_movimento_horizontal(limpar_agachamento=True)
            self.combate.limpar_ataque()
            self.animacao.cancelar_ataque()
            return

        # Leitura da tecla de agachar (S ou Seta para Baixo)
        quer_agachar = bool(teclas[pygame.K_s] or teclas[pygame.K_DOWN])
        self.fisica._intencao_agachar = quer_agachar

        # Só pode agachar quando estiver apoiado no chão
        if quer_agachar and self.fisica.no_chao:
            self.fisica.aplicar_postura_agachado(True, plataformas)
        elif self.fisica.agachado:
            self.fisica.aplicar_postura_agachado(False, plataformas)

        # Enquanto agachado: impede andar, pular e atacar, preservando a direção atual
        if self.fisica.agachado:
            self.fisica.parar_movimento_horizontal()
            return

        # Movimentação horizontal (A / D)
        movimento_x = 0
        if teclas[pygame.K_a]:
            movimento_x -= 1
        if teclas[pygame.K_d]:
            movimento_x += 1
        self.fisica.definir_movimento_horizontal(movimento_x)

        # Pulo (W ou Barra de Espaço)
        if (teclas[pygame.K_w] or teclas[pygame.K_SPACE]) and self.fisica.no_chao:
            self.pular()

        # Ataque (J ou Tecla F)
        if teclas[pygame.K_j] or teclas[pygame.K_f]:
            self.atacar()

    def pular(self):
        """Executa o pulo caso o personagem esteja vivo, no chão e não agachado."""
        self.fisica.pular(self.esta_vivo)

    def atacar(self):
        """Dispara um ataque e inicia a animação ATTACK caso fora de cooldown."""
        iniciou, tempo_atual = self.combate.atacar(agachado=self.fisica.agachado)
        if iniciou:
            self.animacao.iniciar_ataque(tempo_atual)
        return iniciou

    def movimentar_horizontal(self, dt):
        """Aplica o deslocamento horizontal com base em dt e sincroniza rect.x."""
        self.fisica.movimentar_horizontal(dt)

    def resolver_colisoes_horizontais(self, plataformas, largura_tela=LARGURA):
        """Resolve colisões no eixo X contra plataformas/paredes e limites horizontais."""
        self.fisica.resolver_colisoes_horizontais(plataformas, largura_tela=largura_tela)

    def aplicar_fisica(self, dt):
        """Aplica gravidade contínua, deslocamento vertical e sincroniza rect.y."""
        self.fisica.aplicar_fisica(dt)

    def resolver_colisoes_verticais(self, plataformas=None, chao_provisorio=None):
        """Resolve colisões no eixo Y (chão, teto e CHAO_Y padrão)."""
        self.fisica.resolver_colisoes_verticais(
            plataformas=plataformas,
            chao_provisorio=chao_provisorio,
        )

    def resolver_colisoes_plataformas(self, lista_rects_chao):
        """Compatibilidade: executa resolução vertical contra lista_rects_chao."""
        self.fisica.resolver_colisoes_verticais(plataformas=lista_rects_chao)

    def limitar_tela(self, largura_tela=LARGURA, altura_tela=ALTURA, chao_provisorio=None):
        """Compatibilidade: aplica limites horizontais e chão provisório."""
        self.fisica.resolver_colisoes_horizontais(plataformas=None, largura_tela=largura_tela)
        if chao_provisorio is not None:
            self.fisica.resolver_colisoes_verticais(
                plataformas=None,
                chao_provisorio=chao_provisorio,
            )

    def sincronizar_rect(self):
        """Atualiza a posição do rect de colisão a partir das coordenadas float x e y."""
        self.fisica.sincronizar_rect()

    def atualizar_hitbox_ataque(self):
        """Atualiza a área de dano do ataque e encerra o estado ativo ao expirar."""
        self.combate.atualizar_hitbox_ataque(
            rect_corpo=self.fisica.rect,
            olhando_para_esquerda=self.fisica.olhando_para_esquerda,
        )

    def atualizar_estado_animacao(self):
        """Seleciona o estado de animação atual (DEAD, ATTACK, JUMP, CROUCH, RUN, STOP)."""
        self.animacao.atualizar_estado_animacao(
            esta_vivo=self.esta_vivo,
            no_chao=self.fisica.no_chao,
            agachado=self.fisica.agachado,
            estado_movimento=self.fisica.estado_movimento,
        )

    def atualizar_animacao(self):
        """Avança os frames da animação atual e sincroniza self.imagem."""
        self.animacao.atualizar_animacao(
            esta_vivo=self.esta_vivo,
            no_chao=self.fisica.no_chao,
            agachado=self.fisica.agachado,
            estado_movimento=self.fisica.estado_movimento,
        )
        self._atualizar_imagem_atual()

    def obter_dados_ataque(self):
        """Retorna dicionário {ativo, hitbox, dano, id_ataque} para o módulo de inimigos."""
        return self.combate.obter_dados_ataque()

    def registrar_acerto_ataque(self, alvo):
        """Registra acerto único por alvo no ataque atual."""
        return self.combate.registrar_acerto_ataque(alvo)

    def receber_dano(self, quantidade=1):
        """Aplica dano ao personagem e bloqueia ações/ataque caso chegue a 0 vidas."""
        morreu = self.combate.receber_dano(quantidade)
        if not self.esta_vivo:
            self.fisica.parar_movimento_horizontal(limpar_agachamento=True)
            self.animacao.cancelar_ataque()
        return morreu

    def atualizar(
        self,
        teclas=None,
        dt=None,
        largura_tela=LARGURA,
        altura_tela=ALTURA,
        chao_provisorio=None,
        plataformas=None,
    ):
        """
        Método central de atualização do Player chamado a cada iteração do Game Loop.

        Ordem do pipeline:
        1. Resolver defaults seguros (teclas, dt limitado a 0.05s).
        2. Processar entrada do jogador.
        3. Movimentar horizontalmente.
        4. Resolver colisões horizontais (paredes e limites).
        5. Aplicar gravidade e movimentar verticalmente.
        6. Resolver colisões verticais (plataformas ou CHAO_Y).
        7. Atualizar hitbox de ataque.
        8. Atualizar estado, animação e self.imagem.
        """
        if teclas is None:
            teclas = pygame.key.get_pressed()
        if dt is None:
            dt = 1.0 / FPS
        dt_seguro = min(max(float(dt), 0.0), self.fisica.dt_maximo)

        self.processar_input(teclas, dt_seguro, plataformas=plataformas)
        self.movimentar_horizontal(dt_seguro)
        self.resolver_colisoes_horizontais(plataformas, largura_tela=largura_tela)
        self.aplicar_fisica(dt_seguro)
        self.resolver_colisoes_verticais(
            plataformas=plataformas,
            chao_provisorio=chao_provisorio,
        )
        self.atualizar_hitbox_ataque()
        self.atualizar_estado_animacao()
        self.atualizar_animacao()

    def desenhar(self, tela, depuracao=False):
        """
        Desenha o personagem na tela utilizando self.imagem alinhada pela base do rect.
        Se depuracao=True, desenha também o rect de colisão e a hitbox de ataque.
        """
        self._atualizar_imagem_atual()
        sprite_desenho = self.imagem

        pos_x_desenho = self.rect.centerx - (sprite_desenho.get_width() // 2)
        pos_y_desenho = self.rect.bottom - sprite_desenho.get_height()

        tela.blit(sprite_desenho, (pos_x_desenho, pos_y_desenho))

        if depuracao:
            # Retângulo de colisão do corpo do Player (Verde; Amarelo durante i-frames)
            cor_rect = (255, 220, 0) if self.invulneravel else (0, 255, 0)
            pygame.draw.rect(tela, cor_rect, self.rect, 2)

            # Hitbox da área ativa de ataque (Vermelho)
            if self.combate.hitbox_ataque is not None:
                pygame.draw.rect(tela, (255, 50, 50), self.combate.hitbox_ataque, 2)
