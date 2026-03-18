# config/params.py
"""All tunable game constants. Edit here to adjust balance and controls."""

# ── Screen ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 256
SCREEN_HEIGHT = 256
FPS           = 30
TILE_SIZE     = 16

# ── Party ───────────────────────────────────────────────────────────────────
MAX_PARTY_SIZE = 6

# ── Field ───────────────────────────────────────────────────────────────────
ENCOUNTER_RATE = 0.10   # probability per step in grass

# ── Tile IDs (must match game.pyxres tile sheet) ────────────────────────────
TILE_WALKABLE = list(range(0, 16))    # plain ground, paths
TILE_GRASS    = list(range(16, 20))   # tall grass — triggers encounters
TILE_BLOCK    = list(range(32, 64))   # walls, water, trees — impassable
TILE_WARP     = list(range(64, 68))   # area transition tiles

# ── Area spawn coordinates (tile coords) ────────────────────────────────────
AREA_SPAWN = {
    "field_1": {
        "default":      (5, 5),   # new game / title start
        "from_cave_1":  (30, 16), # returning from cave
    },
    "cave_1": {
        "from_field_1": (1, 10),  # entering cave
    },
}

# ── Battle ──────────────────────────────────────────────────────────────────
CAPTURE_BASE_MULTIPLIER = 1.0
EXP_GAIN_MULTIPLIER     = 1.0
DAMAGE_RANDOM_MIN       = 0.85   # lower bound of damage roll (0.85–1.0)

# ── Keys (pyxel KEY_ integer constants) ─────────────────────────────────────
# These values match pyxel's KEY_* constants; listed explicitly so this file
# can be imported in tests without requiring a live Pyxel display.
KEY_CONFIRM     = [13, 32]              # KEY_RETURN, KEY_SPACE
KEY_CANCEL      = [113]                 # KEY_Q
KEY_MENU        = [101]                 # KEY_E
KEY_MOVE_UP     = [1073741906, 119]     # KEY_UP,    KEY_W
KEY_MOVE_DOWN   = [1073741905, 115]     # KEY_DOWN,  KEY_S
KEY_MOVE_LEFT   = [1073741904, 97]      # KEY_LEFT,  KEY_A
KEY_MOVE_RIGHT  = [1073741903, 100]     # KEY_RIGHT, KEY_D
