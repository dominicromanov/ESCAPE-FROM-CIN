class game_object:
    def __init__(self, imagem):
        self.imagem = imagem
        self.rect = imagem.get_rect()

    def atualizar(self, velocidade_mundo):
        pass

    def desenhar(self, tela):
        tela.blit(self.imagem, self.rect)