# scenes/field_scene.py
"""Field exploration: map rendering, player movement, camera, encounter trigger."""
from __future__ import annotations
import random
import pyxel
from scene_manager import Scene, SceneManager
from gfx import jtext, text_width
from models.player import Player
from models.monster import create_monster
from data.monsters import MONSTERS, pick_encounter
from config.params import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    TILE_GRASS, TILE_BLOCK, TILE_WARP,
    ENCOUNTER_RATE, AREA_SPAWN,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT, KEY_MENU,
)
from save import save_game

AREA_MAP_BANK = {
    "field_1": 0,
    "cave_1":  1,
}
AREA_SIZE = {
    "field_1": (32, 32),
    "cave_1":  (20, 20),
}
AREA_WARP_DEST = {
    "field_1": "cave_1",
    "cave_1":  "field_1",
}

# エンカウントフラッシュのフレーム数（白黒を交互に）
_FLASH_FRAMES = 24


class FieldScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self._flash_timer = 0
        self._flash_wild = None

    @property
    def player(self) -> Player:
        return self.player_ref[0]

    def on_enter(self, **kwargs) -> None:
        self._flash_timer = 0
        self._flash_wild = None

    def on_exit(self) -> None:
        pass

    def update(self) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= 1
            if self._flash_timer == 0 and self._flash_wild is not None:
                wild = self._flash_wild
                self._flash_wild = None
                self.sm.switch("battle", wild_monster=wild)
            return  # フラッシュ中は移動・メニュー不可

        self._handle_move()
        self._check_menu()

    def _any_key(self, keys: list[int]) -> bool:
        """移動キー：最初の1歩は即時、押しっぱなしは短インターバルでリピート。"""
        return any(pyxel.btnp(k, 10, 4) for k in keys)

    def _handle_move(self) -> None:
        dx, dy = 0, 0
        if self._any_key(KEY_MOVE_UP):      dy = -1
        elif self._any_key(KEY_MOVE_DOWN):  dy = 1
        elif self._any_key(KEY_MOVE_LEFT):  dx = -1
        elif self._any_key(KEY_MOVE_RIGHT): dx = 1
        else:
            return

        nx = self.player.pos[0] + dx
        ny = self.player.pos[1] + dy

        mw, mh = AREA_SIZE[self.player.area]
        if not (0 <= nx < mw and 0 <= ny < mh):
            return

        tile = self._get_tile(nx, ny)
        if tile in TILE_BLOCK:
            return

        self.player.pos = [nx, ny]

        if tile in TILE_WARP:
            self._warp()
            return

        if tile in TILE_GRASS:
            self._check_encounter()

    def _get_tile(self, tx: int, ty: int) -> int:
        bank = AREA_MAP_BANK[self.player.area]
        scale = TILE_SIZE // 8  # game tiles are 16px; Pyxel tilemap uses 8px cells
        u, v = pyxel.tilemaps[bank].pget(tx * scale, ty * scale)
        return (v // 8) * 32 + (u // 8)

    def _check_encounter(self) -> None:
        if random.random() >= ENCOUNTER_RATE:
            return
        wild_spec = pick_encounter(self.player.area)
        base_level = self.player.active_monster.level if self.player.active_monster else 5
        wild_level = max(2, base_level + random.randint(-2, 2))
        from data.moves import MOVES
        wild_move_ids = [mid for (lv, mid) in wild_spec.learnable_moves if lv <= wild_level][:4] or [1]
        wild_moves = [MOVES[mid] for mid in wild_move_ids if mid in MOVES][:4]
        if not wild_moves:
            wild_moves = [MOVES[1]]
        self._flash_wild = create_monster(wild_spec, wild_level, wild_moves)
        self._flash_timer = _FLASH_FRAMES  # フラッシュ開始

    def _warp(self) -> None:
        dest = AREA_WARP_DEST[self.player.area]
        from_key = f"from_{self.player.area}"
        spawn = AREA_SPAWN.get(dest, {}).get(from_key, (1, 1))
        self.player.area = dest
        self.player.pos = list(spawn)
        save_game(self.player)

    def _check_menu(self) -> None:
        if self._any_key(KEY_MENU):
            self.sm.switch("menu", return_scene="field")

    def draw(self) -> None:
        pyxel.cls(0)
        mw, mh = AREA_SIZE[self.player.area]
        bank = AREA_MAP_BANK[self.player.area]
        cam_x = max(0, min(self.player.pos[0] - SCREEN_WIDTH // (2 * TILE_SIZE),
                           mw - SCREEN_WIDTH // TILE_SIZE))
        cam_y = max(0, min(self.player.pos[1] - SCREEN_HEIGHT // (2 * TILE_SIZE),
                           mh - SCREEN_HEIGHT // TILE_SIZE))
        pyxel.bltm(0, 0, bank,
                   cam_x * TILE_SIZE, cam_y * TILE_SIZE,
                   SCREEN_WIDTH, SCREEN_HEIGHT, 0)

        sx = (self.player.pos[0] - cam_x) * TILE_SIZE
        sy = (self.player.pos[1] - cam_y) * TILE_SIZE
        pyxel.blt(sx, sy, 1, 0, 0, TILE_SIZE, TILE_SIZE, 0)

        area_names = {"field_1": "そうげん", "cave_1": "どうくつ"}
        name = area_names.get(self.player.area, self.player.area)
        jtext(SCREEN_WIDTH - text_width(name) - 4, 2, name, 7)

        # エンカウントフラッシュ：白黒を4フレームごとに交互
        if self._flash_timer > 0:
            flash_color = 7 if (self._flash_timer // 4) % 2 == 0 else 0
            pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, flash_color)
