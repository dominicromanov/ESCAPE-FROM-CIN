import pygame


class Colision:
    def __init__(self, jogador, inimigo):
        self.jogador = jogador
        self.inimigo = inimigo

    def detectar_colisao(self):
        return pygame.Rect.colliderect(self.jogador.rect, self.inimigo.rect)

    def verificar_ataque_player(self):
        """Verifica se a hitbox do ataque do player atingiu o corpo do inimigo."""
        if not self.inimigo.esta_vivo:
            return

        dados_ataque = self.jogador.obter_dados_ataque()
        if dados_ataque["ativo"] and dados_ataque["hitbox"] is not None:
            if self.inimigo.rect.colliderect(dados_ataque["hitbox"]):
                # Garante que o mesmo soco não acerte o inimigo várias vezes
                if self.jogador.registrar_acerto_ataque(self.inimigo):
                    self.inimigo.receber_dano(dados_ataque["dano"])

    def verificar_ataque_inimigo(self):
        """Verifica se a hitbox do ataque do inimigo atingiu o corpo do player."""
        if not self.inimigo.esta_vivo:
            return

        dados_ataque = self.inimigo.obter_dados_ataque()
        if dados_ataque["ativo"] and dados_ataque["hitbox"] is not None:
            if self.jogador.rect.colliderect(dados_ataque["hitbox"]):
                self.jogador.receber_dano(dados_ataque["dano"])
                self.inimigo.registrar_acerto()