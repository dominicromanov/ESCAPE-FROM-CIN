"""
Pacote do subsistema do Player no ESCAPE-FROM-CIN.

Exporta a classe principal Player e seus componentes modulares:
- PlayerAnimation: sprites, frames, orientação e estados visuais.
- PlayerPhysics: física, gravidade, pulo, agachamento e colisões.
- PlayerCombat: vidas, dano, invulnerabilidade e hitboxes de ataque.
"""

from .player import Player
from .player_animation import PlayerAnimation
from .player_combat import PlayerCombat
from .player_physics import PlayerPhysics

__all__ = ["Player", "PlayerAnimation", "PlayerPhysics", "PlayerCombat"]
