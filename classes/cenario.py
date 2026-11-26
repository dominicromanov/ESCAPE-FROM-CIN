import pygame

class Cenario(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()

        self.image = pygame.image.load('assets/images/CenarioProlongado.png')
        self.rect = self.image.get_rect()


        self.rect.x = x
        self.rect.y = y

    def atualizar(self, cenario2):
        self.rect.x -=3
        self.cenario2 = cenario2
        if self.rect.right <=0:
            self.rect.x = self.cenario2.rect.right

    def desenha_cenario(self, tela):

        tela.blit(self.image, self.rect)

        