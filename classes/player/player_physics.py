import pygame

from constants import LARGURA, CHAO_Y


class PlayerPhysics:
    """
    Componente responsável pela física e hitbox do Player:
    - Coordenadas float sincronizadas com pygame.Rect (60x140 normal, 60x96 agachado).
    - Movimentação horizontal e vertical com separação de eixos e delta time limitado.
    - Gravidade, pulo sem pulo duplo, agachamento com verificação de teto.
    - Colisões com plataformas, paredes, teto, limites da tela e chão padrão CHAO_Y.
    """

    def __init__(self, x=100, y=None):
        self.largura = 60
        self.altura_normal = 140
        self.altura_agachado = 96
        self.altura = self.altura_normal
        self.x = float(x)
        # Se y não for informado, nasce apoiado no chão padrão CHAO_Y
        self.y = float(CHAO_Y - self.altura_normal) if y is None else float(y)
        self.rect = pygame.Rect(round(self.x), round(self.y), self.largura, self.altura)

        self.velocidade_horizontal = 300.0  # Pixels por segundo (~5 px/frame a 60 FPS)
        self.velocidade_vertical = 0.0      # Velocidade atual no eixo Y (pixels/segundo)
        self.velocidade_x_atual = 0.0       # Velocidade atual no eixo X (pixels/segundo)
        self.gravidade = 1200.0             # Aceleração da gravidade (pixels/s²)
        self.forca_pulo = -650.0            # Impulso vertical inicial para o pulo
        self.dt_maximo = 0.05               # Limite de delta time para evitar tunelamento (20 FPS)
        self.no_chao = False                # Indica se o personagem está apoiado em superfície sólida

        self.olhando_para_esquerda = False
        self.estado_movimento = "PARADO"    # "PARADO" ou "ANDANDO"
        self.agachado = False               # Indica se o personagem está atualmente agachado
        self._intencao_agachar = False      # Indica se a tecla de agachar está pressionada
        self._intencao_movimento_x = 0      # Direção horizontal solicitada no frame (-1, 0 ou 1)

    def parar_movimento_horizontal(self, limpar_agachamento=False):
        """Zera a intenção e velocidade horizontal (usado ao agachar ou morrer)."""
        if limpar_agachamento:
            self._intencao_agachar = False
        self._intencao_movimento_x = 0
        self.velocidade_x_atual = 0.0
        self.estado_movimento = "PARADO"

    def definir_movimento_horizontal(self, direcao):
        """Define a direção horizontal (-1, 0 ou 1), velocidade X, orientação e estado."""
        self._intencao_movimento_x = direcao
        self.velocidade_x_atual = direcao * self.velocidade_horizontal

        if direcao < 0:
            self.olhando_para_esquerda = True
            self.estado_movimento = "ANDANDO"
        elif direcao > 0:
            self.olhando_para_esquerda = False
            self.estado_movimento = "ANDANDO"
        else:
            self.estado_movimento = "PARADO"

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

    def aplicar_postura_agachado(self, agachar, plataformas=None):
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

    def pular(self, esta_vivo):
        """Executa o pulo caso o personagem esteja vivo, no chão e não agachado."""
        if esta_vivo and self.no_chao and not self.agachado:
            self.velocidade_vertical = self.forca_pulo
            self.no_chao = False

    def movimentar_horizontal(self, dt):
        """Aplica o deslocamento horizontal com base em dt e sincroniza rect.x."""
        self.x += self.velocidade_x_atual * dt
        self.rect.x = round(self.x)

    def resolver_colisoes_horizontais(self, plataformas, largura_tela=LARGURA):
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
        Quando nenhuma coleção de plataformas nem chao_provisorio é informada,
        utiliza CHAO_Y de constants.py como chão padrão do jogo.
        """
        self.no_chao = False

        if plataformas is not None:
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

        # Chão efetivo: usa chao_provisorio se explícito, ou CHAO_Y quando sem plataformas
        limite_chao = chao_provisorio
        if limite_chao is None and plataformas is None:
            limite_chao = CHAO_Y

        if limite_chao is not None:
            if self.rect.bottom >= limite_chao:
                self.rect.bottom = int(limite_chao)
                self.y = float(self.rect.y)
                self.velocidade_vertical = 0.0
                self.no_chao = True

    def sincronizar_rect(self):
        """Atualiza a posição do rect de colisão a partir das coordenadas float x e y."""
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)
