import pygame


class PlayerCombat:
    """
    Componente responsável pelo combate e sobrevivência do Player:
    - Sistema padronizado de 3 vidas com invulnerabilidade temporária (i-frames de 1000 ms).
    - Ataque com cooldown (400 ms), janela ativa de hitbox (180 ms) e alcance direcional.
    - Controle de acerto único por golpe via id_ataque e registro de alvos atingidos.
    """

    def __init__(self):
        self.vida_maxima = 3
        self.vida = self.vida_maxima
        self.duracao_invulnerabilidade_ms = 1000  # Janela de i-frames após receber dano
        self.ultimo_dano_tempo = -self.duracao_invulnerabilidade_ms

        self.dano_ataque = 25
        self.atacando = False               # Período ativo da hitbox de ataque (180 ms)
        self.duracao_ataque_ms = 180        # Duração ativa da hitbox de dano
        self.tempo_recarga_ataque_ms = 400  # Cooldown entre ataques
        self.ultimo_ataque_tempo = -self.tempo_recarga_ataque_ms
        self.alcance_ataque_largura = 50
        self.alcance_ataque_altura = 80
        self.hitbox_ataque = None           # Retângulo da área de dano do ataque
        self.id_ataque = 0                  # Identificador incremental único por ataque disparado
        self._alvos_atingidos_no_ataque = set()

    @property
    def esta_vivo(self):
        """Retorna True se o personagem ainda possui pontos de vida positivos."""
        return self.vida > 0

    @property
    def invulneravel(self):
        """Retorna True enquanto o personagem estiver na janela de invulnerabilidade (i-frames)."""
        if not self.esta_vivo:
            return False
        tempo_atual = pygame.time.get_ticks()
        return (tempo_atual - self.ultimo_dano_tempo) < self.duracao_invulnerabilidade_ms

    def limpar_ataque(self):
        """Encerra estado de ataque ativo e remove a hitbox de dano."""
        self.atacando = False
        self.hitbox_ataque = None

    def atacar(self, agachado):
        """
        Dispara um ataque caso o personagem esteja vivo, não agachado e fora do cooldown.
        Retorna (iniciou: bool, tempo_atual: int).
        """
        tempo_atual = pygame.time.get_ticks()
        if not self.esta_vivo or agachado:
            return False, tempo_atual

        if tempo_atual - self.ultimo_ataque_tempo >= self.tempo_recarga_ataque_ms:
            self.atacando = True
            self.ultimo_ataque_tempo = tempo_atual
            self.id_ataque += 1
            self._alvos_atingidos_no_ataque.clear()
            return True, tempo_atual
        return False, tempo_atual

    def atualizar_hitbox_ataque(self, rect_corpo, olhando_para_esquerda):
        """Atualiza a área de dano do ataque e encerra o estado ativo ao expirar."""
        if not self.esta_vivo:
            self.limpar_ataque()
            return

        tempo_atual = pygame.time.get_ticks()
        if self.atacando:
            if tempo_atual - self.ultimo_ataque_tempo <= self.duracao_ataque_ms:
                if olhando_para_esquerda:
                    hitbox_x = rect_corpo.left - self.alcance_ataque_largura
                else:
                    hitbox_x = rect_corpo.right

                hitbox_y = rect_corpo.centery - (self.alcance_ataque_altura // 2)
                self.hitbox_ataque = pygame.Rect(
                    hitbox_x, hitbox_y, self.alcance_ataque_largura, self.alcance_ataque_altura
                )
            else:
                self.limpar_ataque()
        else:
            self.hitbox_ataque = None

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

    def receber_dano(self, quantidade=1):
        """
        Aplica dano ao personagem no sistema padronizado de 3 vidas:
        - Ignora quantidades inválidas (não numéricas, booleanas ou <= 0).
        - Ignora dano se o personagem já estiver morto ou em invulnerabilidade (i-frames).
        - Cada dano válido remove exatamente 1 vida, nunca deixando a vida negativa
          nem acima de vida_maxima.
        - Ativa a janela de invulnerabilidade temporária (`duracao_invulnerabilidade_ms`).
        - Retorna True se o personagem morreu (vida == 0), False caso contrário.
        """
        if not isinstance(quantidade, (int, float)) or isinstance(quantidade, bool):
            return not self.esta_vivo

        if quantidade <= 0:
            return not self.esta_vivo

        if not self.esta_vivo:
            return True

        if self.invulneravel:
            return False

        self.vida = max(0, min(self.vida_maxima, self.vida - 1))
        self.ultimo_dano_tempo = pygame.time.get_ticks()

        if not self.esta_vivo:
            self.limpar_ataque()
        return not self.esta_vivo
