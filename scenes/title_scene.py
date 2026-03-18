# scenes/title_scene.py
"""Title screen, new game / continue selection, player name input, starter pick."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from gfx import jtext, text_width
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

# 50音グリッド（5列）＋最終行にアクションボタン
_KANA_GRID: list[list[str | None]] = [
    list("あいうえお"),
    list("かきくけこ"),
    list("さしすせそ"),
    list("たちつてと"),
    list("なにぬねの"),
    list("はひふへほ"),
    list("まみむめも"),
    list("やゆよ") + [None, None],
    list("らりるれろ"),
    list("わをん") + [None, None],
    ["けす", None, None, None, "けってい"],  # アクション行
]
_ACTION_ROW = len(_KANA_GRID) - 1

# グリッド描画定数
_GX = 20        # グリッド左端 x
_GY = 46        # グリッド上端 y
_CW = 22        # セル幅
_CH = 14        # セル高さ


def _row_len(row: list) -> int:
    return sum(1 for c in row if c is not None)


def _nth_valid(row: list, n: int) -> int:
    """row の中で n 番目(0始まり)の非Noneのインデックスを返す。"""
    count = 0
    for i, c in enumerate(row):
        if c is not None:
            if count == n:
                return i
            count += 1
    return 0


def _valid_idx(row: list, col: int) -> int:
    """col が None なら左右の最も近い有効インデックスに補正する。"""
    if row[col] is not None:
        return col
    # 左を探す
    for c in range(col - 1, -1, -1):
        if row[c] is not None:
            return c
    # 右を探す
    for c in range(col + 1, len(row)):
        if row[c] is not None:
            return c
    return 0


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
        self.kana_row = 0
        self.kana_col = 0
        self.existing_save = False

    def on_enter(self, **kwargs) -> None:
        self.phase = TitlePhase.SPLASH
        self.cursor = 0
        self.player_name = ""
        self.kana_row = 0
        self.kana_col = 0
        self.existing_save = load_game() is not None

    def on_exit(self) -> None:
        pass

    def _press(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

    def _repeat(self, keys: list[int]) -> bool:
        """押しっぱなしリピート（0.5s後に10fps）。"""
        return any(pyxel.btnp(k, 15, 3) for k in keys)

    def update(self) -> None:
        if self.phase == TitlePhase.SPLASH:
            if self._press(KEY_CONFIRM):
                if self.existing_save:
                    self.phase = TitlePhase.CHOICE
                    self.cursor = 0
                else:
                    self.phase = TitlePhase.NAME

        elif self.phase == TitlePhase.CHOICE:
            if self._repeat(KEY_MOVE_UP) or self._repeat(KEY_MOVE_DOWN):
                self.cursor ^= 1
            if self._press(KEY_CONFIRM):
                if self.cursor == 0:
                    player = load_game()
                    self.player_ref[0] = player
                    self.sm.switch("field")
                else:
                    self.phase = TitlePhase.NAME
                    self.cursor = 0

        elif self.phase == TitlePhase.NAME:
            self._update_name()

        elif self.phase == TitlePhase.STARTER:
            if self._repeat(KEY_MOVE_LEFT):
                self.cursor = (self.cursor - 1) % 3
            if self._repeat(KEY_MOVE_RIGHT):
                self.cursor = (self.cursor + 1) % 3
            if self._press(KEY_CONFIRM):
                self._start_new_game(self.cursor)

    def _update_name(self) -> None:
        row = self.kana_row
        col = self.kana_col

        if self._repeat(KEY_MOVE_UP):
            row = max(0, row - 1)
            col = _valid_idx(_KANA_GRID[row], min(col, len(_KANA_GRID[row]) - 1))
        if self._repeat(KEY_MOVE_DOWN):
            row = min(_ACTION_ROW, row + 1)
            col = _valid_idx(_KANA_GRID[row], min(col, len(_KANA_GRID[row]) - 1))
        if self._repeat(KEY_MOVE_LEFT):
            col = col - 1
            while col >= 0 and _KANA_GRID[row][col] is None:
                col -= 1
            col = max(0, col)
            col = _valid_idx(_KANA_GRID[row], col)
        if self._repeat(KEY_MOVE_RIGHT):
            col = col + 1
            while col < len(_KANA_GRID[row]) and _KANA_GRID[row][col] is None:
                col += 1
            if col >= len(_KANA_GRID[row]):
                col = len(_KANA_GRID[row]) - 1
            col = _valid_idx(_KANA_GRID[row], col)

        self.kana_row = row
        self.kana_col = col

        if self._press(KEY_CONFIRM):
            ch = _KANA_GRID[self.kana_row][self.kana_col]
            if ch == "けってい":
                if self.player_name:
                    self.phase = TitlePhase.STARTER
                    self.cursor = 0
            elif ch == "けす":
                if self.player_name:
                    self.player_name = self.player_name[:-1]
            elif ch and len(self.player_name) < 8:
                self.player_name += ch

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

    # ── 描画 ────────────────────────────────────────────────────────────────

    def draw(self) -> None:
        pyxel.cls(0)
        if self.phase == TitlePhase.SPLASH:
            jtext(SCREEN_WIDTH // 2 - 8, 80, "MON", 10)
            jtext(SCREEN_WIDTH // 2 - 28, 100, "Press Enter", 7)

        elif self.phase == TitlePhase.CHOICE:
            jtext(80, 80,  (">" if self.cursor == 0 else " ") + "つづきから", 7)
            jtext(80, 96,  (">" if self.cursor == 1 else " ") + "はじめから", 7)

        elif self.phase == TitlePhase.NAME:
            self._draw_name()

        elif self.phase == TitlePhase.STARTER:
            jtext(8, 8, "さいしょの モンスターを えらんで！", 7)
            for i, (sid, stype) in enumerate(zip(_STARTERS, _STARTER_TYPES)):
                spec = MONSTERS[sid]
                x = 16 + i * 80
                color = 10 if i == self.cursor else 7
                prefix = ">" if i == self.cursor else " "
                jtext(x, 80, prefix + spec.name, color)
                jtext(x + 4, 92, stype, 13)

    def _draw_name(self) -> None:
        # ヘッダー
        jtext(8, 4, "なまえを いれてね", 7)

        # 入力中の名前
        pyxel.rect(8, 16, SCREEN_WIDTH - 16, 12, 1)
        name_str = self.player_name + ("_" if pyxel.frame_count % 30 < 15 else " ")
        jtext(12, 18, name_str, 10)

        # 50音グリッド
        for row_i, row in enumerate(_KANA_GRID):
            for col_i, ch in enumerate(row):
                if ch is None:
                    continue
                if row_i == _ACTION_ROW:
                    # アクション行は左右端に配置
                    if col_i == 0:
                        x = _GX
                    else:
                        x = SCREEN_WIDTH - text_width(ch) - _GX
                else:
                    x = _GX + col_i * _CW
                y = _GY + row_i * _CH

                selected = (row_i == self.kana_row and col_i == self.kana_col)
                if selected:
                    pyxel.rect(x - 2, y - 1, text_width(ch) + 3, _CH - 1, 2)
                color = 10 if selected else (9 if row_i == _ACTION_ROW else 7)
                jtext(x, y, ch, color)
