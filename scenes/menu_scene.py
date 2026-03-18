# scenes/menu_scene.py
"""In-game menu: party, Pokedex, bag, save."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from gfx import jtext
from models.player import Player
from data.monsters import MONSTERS
from save import save_game
from config.params import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_CONFIRM, KEY_CANCEL, KEY_MOVE_UP, KEY_MOVE_DOWN

_MAIN_ITEMS = ["てもち", "ずかん", "バッグ", "セーブ", "もどる"]


class MenuPhase:
    MAIN  = "main"
    PARTY = "party"
    DEX   = "dex"
    BAG   = "bag"


class MenuScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self.return_scene = "field"
        self.phase = MenuPhase.MAIN
        self.cursor = 0
        self.save_msg = ""
        self.save_msg_timer = 0

    @property
    def player(self) -> Player:
        return self.player_ref[0]

    def on_enter(self, return_scene: str = "field", **kwargs) -> None:
        self.return_scene = return_scene
        self.phase = MenuPhase.MAIN
        self.cursor = 0

    def on_exit(self) -> None:
        pass

    def _any(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

    def _any_repeat(self, keys: list[int]) -> bool:
        """カーソル移動用：押しっぱなしリピート。"""
        return any(pyxel.btnp(k, 14, 4) for k in keys)

    def update(self) -> None:
        if self.save_msg_timer > 0:
            self.save_msg_timer -= 1

        if self.phase == MenuPhase.MAIN:
            self._update_main()
        elif self.phase in (MenuPhase.PARTY, MenuPhase.DEX, MenuPhase.BAG):
            if self._any(KEY_CANCEL) or self._any(KEY_CONFIRM):
                self.phase = MenuPhase.MAIN

    def _update_main(self) -> None:
        n = len(_MAIN_ITEMS)
        if self._any_repeat(KEY_MOVE_UP):     self.cursor = (self.cursor - 1) % n
        elif self._any_repeat(KEY_MOVE_DOWN): self.cursor = (self.cursor + 1) % n
        elif self._any(KEY_CANCEL):
            self.sm.switch(self.return_scene)
        elif self._any(KEY_CONFIRM):
            if   self.cursor == 0: self.phase = MenuPhase.PARTY
            elif self.cursor == 1: self.phase = MenuPhase.DEX
            elif self.cursor == 2: self.phase = MenuPhase.BAG
            elif self.cursor == 3:
                save_game(self.player)
                self.save_msg = "セーブしました！"
                self.save_msg_timer = 90
            elif self.cursor == 4:
                self.sm.switch(self.return_scene)

    def draw(self) -> None:
        pyxel.cls(1)
        if self.phase == MenuPhase.MAIN:   self._draw_main()
        elif self.phase == MenuPhase.PARTY: self._draw_party()
        elif self.phase == MenuPhase.DEX:   self._draw_dex()
        elif self.phase == MenuPhase.BAG:   self._draw_bag()

    def _draw_main(self) -> None:
        jtext(8, 8, "メニュー", 7)
        for i, item in enumerate(_MAIN_ITEMS):
            prefix = ">" if i == self.cursor else " "
            jtext(16, 24 + i * 12, prefix + item, 7)
        if self.save_msg_timer > 0:
            jtext(8, SCREEN_HEIGHT - 12, self.save_msg, 10)

    def _draw_party(self) -> None:
        jtext(8, 8, "てもち", 7)
        for i, mon in enumerate(self.player.party):
            y = 24 + i * 22
            jtext(8, y,      mon.spec.name, 7)
            jtext(8, y + 11, f"Lv{mon.level}  HP{mon.current_hp}/{mon.max_hp}", 13)

    def _draw_dex(self) -> None:
        jtext(8, 8, "ずかん", 7)
        jtext(8, 20, f"つかまえた: {len(self.player.caught_ids)}ひき", 7)
        for i, mid in enumerate(sorted(self.player.caught_ids)):
            if mid in MONSTERS:
                jtext(8, 32 + i * 10, f"No.{mid:03d} {MONSTERS[mid].name}", 7)

    def _draw_bag(self) -> None:
        jtext(8, 8, "バッグ", 7)
        y = 24
        for item, count in self.player.items.items():
            label = "モンスターボール" if item == "pokeball" else item
            jtext(8, y, f"{label} x{count}", 7)
            y += 12
