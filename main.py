# main.py
"""Entry point: initialize Pyxel, wire scenes, start game loop."""
import pyxel
from config.params import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from scene_manager import SceneManager
from models.player import Player
from scenes.title_scene import TitleScene
from scenes.field_scene import FieldScene
from scenes.battle_scene import BattleScene
from scenes.menu_scene import MenuScene


def main():
    pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="MON", fps=FPS)
    pyxel.load("assets/game.pyxres")

    sm = SceneManager()

    # Shared player reference: TitleScene sets [0], all others read via .player property
    player_ref: list[Player | None] = [None]

    title  = TitleScene(sm, player_ref)
    field  = FieldScene(sm, player_ref)
    battle = BattleScene(sm, player_ref)
    menu   = MenuScene(sm, player_ref)

    sm.register("title",  title)
    sm.register("field",  field)
    sm.register("battle", battle)
    sm.register("menu",   menu)

    sm.switch("title")

    pyxel.run(sm.update, sm.draw)


if __name__ == "__main__":
    main()
