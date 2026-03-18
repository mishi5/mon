#!/usr/bin/env python3
"""
Generate assets/game.pyxres programmatically.

Tile ID layout (matches config/params.py):
  Row 0 (v=0):  IDs  0-15  WALKABLE  cols 0-15  (u=0..120)
                IDs 16-19  GRASS     cols 16-19  (u=128..152)
  Row 1 (v=8):  IDs 32-63  BLOCK     cols 0-31   (u=0..248)
  Row 2 (v=16): IDs 64-67  WARP      cols 0-3    (u=0..24)

Tile ID formula: tile_id = (v // 8) * 32 + (u // 8)

Run with: uv run python create_assets.py
"""
import pyxel

# Image pixel coords (u, v) for each tile category
T_WALK = (0,   0)    # tile_id=0   → WALKABLE
T_GRASS = (128, 0)   # tile_id=16  → GRASS
T_WALL = (0,   8)    # tile_id=32  → BLOCK (field wall / tree)
T_CAVE = (8,   8)    # tile_id=33  → BLOCK (cave wall, same range)
T_WARP = (0,  16)    # tile_id=64  → WARP


def _fill(img, u: int, v: int, color: int, border: int = -1) -> None:
    """Fill an 8×8 tile at image pixel (u, v) with a solid color."""
    for dy in range(8):
        for dx in range(8):
            c = color
            if border >= 0 and (dx == 0 or dy == 0 or dx == 7 or dy == 7):
                c = border
            img.pset(u + dx, v + dy, c)


def _draw_grass(img, u: int, v: int) -> None:
    """Draw a stylised grass tile with blade highlights."""
    _fill(img, u, v, 3)                     # dark green base
    for bx in [1, 3, 6]:                    # blade tips
        img.pset(u + bx, v + 1, 11)
        img.pset(u + bx, v + 2, 11)


def _draw_player(img) -> None:
    """Draw a 16×16 player sprite at image (0, 0) in bank 1.

    Color key 0 (black) is transparent when blitting.
    """
    rows = [
        "0000088880000000",
        "0000088880000000",
        "0000888888000000",
        "0000EE8EE8000000",
        "000EEEEEEEE00000",
        "000EEE7EE70 00000",
        "000EEEEEEE000000",
        "000EEEEEEE000000",
        "00CCCCCCCCCC0000",
        "00CCCCCCCCCC0000",
        "00CCCCCCCCCC0000",
        "00CCCCCCCCCC0000",
        "000CC00000CC0000",
        "000CC00000CC0000",
        "000550000055 0000",
        "0000000000000000",
    ]
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch == " ":
                ch = "0"
            img.pset(rx, ry, int(ch, 16))


def _set_game_tile(tm, gx: int, gy: int, u: int, v: int) -> None:
    """Map a 16px game tile at (gx, gy) to four 8×8 Pyxel tilemap cells."""
    px, py = gx * 2, gy * 2
    for dy in range(2):
        for dx in range(2):
            tm.pset(px + dx, py + dy, (u, v))


def _build_field(tm) -> None:
    """32×32 game-tile map for field_1."""
    MW, MH = 32, 32

    # Fill with walkable ground
    for gy in range(MH):
        for gx in range(MW):
            _set_game_tile(tm, gx, gy, *T_WALK)

    # Border walls
    for gx in range(MW):
        _set_game_tile(tm, gx, 0,      *T_WALL)
        _set_game_tile(tm, gx, MH - 1, *T_WALL)
    for gy in range(MH):
        _set_game_tile(tm, 0,      gy, *T_WALL)
        _set_game_tile(tm, MW - 1, gy, *T_WALL)

    # Grass patches (several scattered regions)
    for (x0, y0, x1, y1) in [
        (3,  7,  9,  13),  # left patch (avoids default spawn at 5,5)
        (14, 4,  20, 10),
        (9,  14, 15, 20),
        (5,  20, 11, 26),
        (20, 17, 27, 24),
    ]:
        for gy in range(y0, y1):
            for gx in range(x0, x1):
                _set_game_tile(tm, gx, gy, *T_GRASS)

    # Decorative tree lines (impassable block tiles inside the map)
    for gx in range(8, 14):
        _set_game_tile(tm, gx, 12, *T_WALL)
    for gx in range(18, 24):
        _set_game_tile(tm, gx, 8,  *T_WALL)

    # Cave entrance: open a gap in the right wall at y=16, then place warp
    # AREA_SPAWN["field_1"]["from_cave_1"] = (30, 16)
    _set_game_tile(tm, MW - 1, 16, *T_WALK)  # gap in right wall
    _set_game_tile(tm, 30,     16, *T_WARP)  # warp tile


def _build_cave(tm) -> None:
    """20×20 game-tile map for cave_1."""
    MW, MH = 20, 20

    # Fill with cave wall
    for gy in range(MH):
        for gx in range(MW):
            _set_game_tile(tm, gx, gy, *T_CAVE)

    # Walkable cave floor (interior)
    for gy in range(1, MH - 1):
        for gx in range(1, MW - 1):
            _set_game_tile(tm, gx, gy, *T_WALK)

    # Rock pillars / obstacles
    for (gx, gy) in [
        (4, 4), (4, 5), (5, 4),
        (10, 6), (10, 7), (11, 6),
        (15, 4), (15, 5),
        (7, 12), (8, 12),
        (13, 15), (14, 15), (13, 14),
    ]:
        _set_game_tile(tm, gx, gy, *T_CAVE)

    # Exit warp: AREA_SPAWN["cave_1"]["from_field_1"] = (1, 10)
    _set_game_tile(tm, 1, 10, *T_WARP)


def main() -> None:
    pyxel.init(256, 256, title="Asset Builder")

    # ── Image bank 0: tileset ────────────────────────────────────────────────
    img0 = pyxel.images[0]

    # Walkable ground: bright green with slight variation
    _fill(img0, *T_WALK, color=11, border=3)
    img0.pset(2, 2, 7)   # highlight pixel
    img0.pset(5, 5, 3)   # shadow pixel

    # Grass: dark green base with bright blade tips
    _draw_grass(img0, *T_GRASS)

    # Field wall / tree: dark grey with stone texture
    _fill(img0, *T_WALL, color=5, border=13)
    img0.pset(2, 9, 6)
    img0.pset(5, 12, 13)

    # Cave wall: brown earth tone
    _fill(img0, *T_CAVE, color=4, border=1)
    img0.pset(3, 9, 9)

    # Warp / doorway: warm yellow with bright border
    _fill(img0, *T_WARP, color=10, border=9)
    img0.pset(3, 17, 14)
    img0.pset(4, 18, 10)

    # ── Image bank 1: sprites ────────────────────────────────────────────────
    _draw_player(pyxel.images[1])

    # ── Tilemap bank 0: field_1 ──────────────────────────────────────────────
    _build_field(pyxel.tilemaps[0])

    # ── Tilemap bank 1: cave_1 ───────────────────────────────────────────────
    _build_cave(pyxel.tilemaps[1])

    # ── Save ─────────────────────────────────────────────────────────────────
    pyxel.save("assets/game.pyxres")
    print("✓ assets/game.pyxres saved")


if __name__ == "__main__":
    main()
