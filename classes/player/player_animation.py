from pathlib import Path
import pygame


class PlayerAnimation:
    """
    Componente responsável pelas animações do Player:
    - Carregamento robusto dos 28 sprites em assets/player/ (independente do cwd).
    - Gerenciamento dos estados STOP, RUN, JUMP, CROUCH, ATTACK e DEAD.
    - Controle de temporização por estado (120 ms padrão, 45 ms para ATTACK).
    - Espelhamento horizontal para orientação esquerda/direita.
    """

    def __init__(self):
        self.animacoes = self._carregar_todas_animacoes()
        self.estado_animacao = "STOP"       # "STOP", "RUN", "JUMP", "CROUCH", "ATTACK", "DEAD"
        self.indice_frame = 0
        self.intervalo_animacao_ms = 120    # Tempo entre quadros das animações comuns
        self.intervalo_animacao_ataque_ms = 45  # 8 frames * 45 ms = 360 ms de animação fluida
        self.ultimo_tempo_animacao = pygame.time.get_ticks()
        self.animando_ataque = False        # Controle separado da sequência visual ATTACK

    def _carregar_todas_animacoes(self):
        """
        Carrega todos os 28 sprites organizados em assets/player usando pathlib.Path
        relativo à localização deste módulo (classes/player/player_animation.py).
        """
        raiz_projeto = Path(__file__).resolve().parent.parent.parent
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

        frames_stop = carregar_lista("STOP", "sprite_1_01_", 3)
        altura_referencia = frames_stop[0].get_height()  # 168 px

        # Carrega os 8 frames de ATTACK recortando margens transparentes e ajustando
        # proporcionalmente em memória para combinar com a escala visual do personagem.
        frames_attack = []
        for i in range(1, 9):
            caminho = pasta_sprites / "ATTACK" / f"attack_{i:02d}.png"
            img = pygame.image.load(str(caminho))
            if display_ativo:
                img = img.convert_alpha()
            bbox = img.get_bounding_rect()
            if bbox.width > 0 and bbox.height > 0:
                img = img.subsurface(bbox).copy()
                escala = altura_referencia / bbox.height
                novo_tamanho = (max(1, round(bbox.width * escala)), altura_referencia)
                img = pygame.transform.smoothscale(img, novo_tamanho)
            frames_attack.append(img)

        caminho_crouch = pasta_sprites / "CROUCH" / "sprite_2_03_03.png"
        img_crouch = pygame.image.load(str(caminho_crouch))
        if display_ativo:
            img_crouch = img_crouch.convert_alpha()

        return {
            "STOP": frames_stop,
            "RUN": carregar_lista("RUN", "sprite_2_01_", 7),
            "JUMP": carregar_lista("JUMP", "sprite_1_03_", 4),
            "CROUCH": [img_crouch],
            "ATTACK": frames_attack,
            "DEAD": carregar_lista("FALL", "sprite_2_06_", 5),
        }

    def iniciar_ataque(self, tempo_atual):
        """Inicia ou reinicia a sequência visual ATTACK a partir do frame 0."""
        self.animando_ataque = True
        self.estado_animacao = "ATTACK"
        self.indice_frame = 0
        self.ultimo_tempo_animacao = tempo_atual

    def cancelar_ataque(self):
        """Interrompe imediatamente a animação de ataque (ex.: ao morrer)."""
        self.animando_ataque = False

    def atualizar_estado_animacao(self, esta_vivo, no_chao, agachado, estado_movimento):
        """
        Seleciona a animação correspondente com base na vida, ataque, estado físico e movimento:
        - DEAD: quando a vida chega a zero (prioridade máxima).
        - ATTACK: enquanto a sequência visual de 8 frames do ataque está em andamento.
        - JUMP: durante toda a trajetória aérea (subida e descida).
        - CROUCH: agachado no chão.
        - RUN: andando no chão.
        - STOP: parado no chão.
        """
        if not esta_vivo:
            novo_estado = "DEAD"
        elif self.animando_ataque:
            novo_estado = "ATTACK"
        elif not no_chao:
            novo_estado = "JUMP"
        elif agachado:
            novo_estado = "CROUCH"
        elif estado_movimento == "ANDANDO":
            novo_estado = "RUN"
        else:
            novo_estado = "STOP"

        if novo_estado != self.estado_animacao:
            self.estado_animacao = novo_estado
            self.indice_frame = 0
            self.ultimo_tempo_animacao = pygame.time.get_ticks()

    def atualizar_animacao(self, esta_vivo, no_chao, agachado, estado_movimento):
        """
        Avança os frames da animação atual com base no tempo decorrido.
        - DEAD: reproduz a sequência uma única vez e congela no último frame.
        - ATTACK: reproduz os 8 frames com intervalo próprio (45 ms/frame) e, ao finalizar,
          encerra `animando_ataque` retornando imediatamente à animação do estado atual.
        """
        tempo_atual = pygame.time.get_ticks()
        intervalo = (
            self.intervalo_animacao_ataque_ms
            if self.estado_animacao == "ATTACK"
            else self.intervalo_animacao_ms
        )
        if tempo_atual - self.ultimo_tempo_animacao >= intervalo:
            frames = self.animacoes[self.estado_animacao]
            if self.estado_animacao == "DEAD":
                if self.indice_frame < len(frames) - 1:
                    self.indice_frame += 1
                self.ultimo_tempo_animacao = tempo_atual
            elif self.estado_animacao == "ATTACK":
                if self.indice_frame < len(frames) - 1:
                    self.indice_frame += 1
                    self.ultimo_tempo_animacao = tempo_atual
                else:
                    self.animando_ataque = False
                    self.atualizar_estado_animacao(
                        esta_vivo=esta_vivo,
                        no_chao=no_chao,
                        agachado=agachado,
                        estado_movimento=estado_movimento,
                    )
            else:
                self.indice_frame = (self.indice_frame + 1) % len(frames)
                self.ultimo_tempo_animacao = tempo_atual

    def obter_imagem_atual(self, olhando_para_esquerda):
        """Retorna a Surface do frame atual, espelhada horizontalmente se olhando para a esquerda."""
        frames = self.animacoes[self.estado_animacao]
        frame = frames[self.indice_frame % len(frames)]
        if olhando_para_esquerda:
            return pygame.transform.flip(frame, True, False)
        return frame
