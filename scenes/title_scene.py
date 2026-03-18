# scenes/title_scene.py
"""Title screen, new game / continue selection, player name input, starter pick."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from models.player import Player
from models.monster import create_monster
from data.monsters import MONSTERS
from data.moves import MOVES
from save import save_game, load_game
from config.params import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    KEY_CONFIRM, KEY_CANCEL,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT,
)

_STARTERS = [1, 2, 3]
_STARTER_TYPES = ["ほのお", "みず", "くさ"]

# Hiragana for name input; last entry is the "done" button
_KANA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん") + ["けってい"]
_KANA_DONE = "けってい"


class TitlePhase:
    SPLASH  = "splash"
    CHOICE  = "choice"
    NAME    = "name"
    STARTER = "starter"


class TitleScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self.phase = TitlePhase.SPLASH
        self.cursor = 0
        self.player_name = ""
        self.kana_cursor = 0
        self.existing_save = False

    def on_enter(self, **kwargs) -> None:
        self.phase = TitlePhase.SPLASH
        self.cursor = 0
        self.player_name = ""
        self.kana_cursor = 0
        self.existing_save = load_game() is not None

    def on_exit(self) -> None:
        pass

    def _any(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

    def update(self) -> None:
        if self.phase == TitlePhase.SPLASH:
            if self._any(KEY_CONFIRM):
                if self.existing_save:
                    self.phase = TitlePhase.CHOICE
                    self.cursor = 0
                else:
                    self.phase = TitlePhase.NAME

        elif self.phase == TitlePhase.CHOICE:
            if self._any(KEY_MOVE_UP) or self._any(KEY_MOVE_DOWN):
                self.cursor ^= 1
            if self._any(KEY_CONFIRM):
                if self.cursor == 0:   # つづきから
                    player = load_game()
                    self.player_ref[0] = player
                    self.sm.switch("field")
                else:                  # はじめから
                    self.phase = TitlePhase.NAME
                    self.cursor = 0

        elif self.phase == TitlePhase.NAME:
            if self._any(KEY_MOVE_LEFT):
                self.kana_cursor = max(0, self.kana_cursor - 1)
            if self._any(KEY_MOVE_RIGHT):
                self.kana_cursor = min(len(_KANA) - 1, self.kana_cursor + 1)
            if self._any(KEY_CONFIRM):
                selected = _KANA[self.kana_cursor]
                if selected == _KANA_DONE:
                    if self.player_name:
                        self.phase = TitlePhase.STARTER
                        self.cursor = 0
                elif len(self.player_name) < 8:
                    self.player_name += selected
            if self._any(KEY_CANCEL) and self.player_name:
                self.player_name = self.player_name[:-1]

        elif self.phase == TitlePhase.STARTER:
            if self._any(KEY_MOVE_LEFT):
                self.cursor = (self.cursor - 1) % 3
            if self._any(KEY_MOVE_RIGHT):
                self.cursor = (self.cursor + 1) % 3
            if self._any(KEY_CONFIRM):
                self._start_new_game(self.cursor)

    def _start_new_game(self, starter_idx: int) -> None:
        spec = MONSTERS[_STARTERS[starter_idx]]
        starter_moves = [MOVES[mid] for (lv, mid) in spec.learnable_moves if lv == 1][:4]
        if not starter_moves:
            starter_moves = [MOVES[9]]
        monster = create_monster(spec, level=5, moves=starter_moves)
        player = Player(name=self.player_name, area="field_1", pos=[5, 5])
        player.party.append(monster)
        player.caught_ids = [spec.id]
        save_game(player)
        self.player_ref[0] = player
        self.sm.switch("field")

    def draw(self) -> None:
        pyxel.cls(0)
        if self.phase == TitlePhase.SPLASH:
            pyxel.text(SCREEN_WIDTH // 2 - 8, 80, "MON", 10)
            pyxel.text(SCREEN_WIDTH // 2 - 28, 100, "Press Enter", 7)

        elif self.phase == TitlePhase.CHOICE:
            pyxel.text(80, 80,  (">" if self.cursor == 0 else " ") + "つづきから", 7)
            pyxel.text(80, 96,  (">" if self.cursor == 1 else " ") + "はじめから", 7)

        elif self.phase == TitlePhase.NAME:
            pyxel.text(8, 8, "なまえを いれてね", 7)
            pyxel.text(8, 24, self.player_name + "_", 10)
            start = max(0, self.kana_cursor - 10)
            for i, ch in enumerate(_KANA[start:start + 20]):
                color = 10 if (start + i) == self.kana_cursor else 7
                pyxel.text(8 + i * 12, 48, ch, color)
            pyxel.text(8, 64, "Enter:かくてい  Q:けす", 13)

        elif self.phase == TitlePhase.STARTER:
            pyxel.text(8, 8, "さいしょの モンスターを えらんで！", 7)
            for i, (sid, stype) in enumerate(zip(_STARTERS, _STARTER_TYPES)):
                spec = MONSTERS[sid]
                x = 16 + i * 80
                color = 10 if i == self.cursor else 7
                prefix = ">" if i == self.cursor else " "
                pyxel.text(x, 80, prefix + spec.name, color)
                pyxel.text(x + 4, 92, stype, 13)
