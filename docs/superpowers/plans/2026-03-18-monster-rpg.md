# Monster RPG Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Game Boy-style monster-collecting RPG with field exploration, wild encounters, turn-based battles, and capture mechanics using Pyxel.

**Architecture:** SceneManager pattern — each screen (Title, Field, Battle, Menu) is an isolated Scene with `update()`/`draw()`/`on_enter()`/`on_exit()` lifecycle. Pure logic lives in `models/` and is fully testable without Pyxel. `config/params.py` centralizes all tunable values.

**Tech Stack:** Python 3.12+, Pyxel (latest), uv (package management), pytest

---

## File Map

| File | Responsibility |
|---|---|
| `main.py` | Pyxel init, SceneManager wiring, game loop |
| `scene_manager.py` | Scene registration, switching, lifecycle dispatch |
| `save.py` | JSON save/load, serialization/deserialization |
| `config/params.py` | All tunable constants (tile IDs, key bindings, rates) |
| `models/monster.py` | `MonsterSpec`, `Move`, `Monster` dataclasses + stat formulas |
| `models/player.py` | `Player` class (position, party, items, area) |
| `models/battle.py` | Pure battle logic: damage, capture, exp, level-up |
| `data/type_chart.py` | 18×18 type effectiveness table |
| `data/moves.py` | All move definitions as `dict[int, Move]` |
| `data/monsters.py` | All monster specs + area encounter tables |
| `scenes/title_scene.py` | Title screen, new game / continue selection, name input, starter pick |
| `scenes/field_scene.py` | Map rendering, player movement, camera, encounter trigger |
| `scenes/battle_scene.py` | Battle UI, command selection, turn execution, message display |
| `scenes/menu_scene.py` | Party view, Pokedex, bag, save |
| `tests/test_monster.py` | Stat calculation, exp_to_next, level-up |
| `tests/test_battle_logic.py` | Damage calc, capture probability, exp gain |
| `tests/test_type_chart.py` | Type effectiveness lookups |
| `tests/test_save.py` | Save/load round-trip, corrupt-file handling |

---

## Chunk 1: Project Foundation

### Task 1: Initialize repo and package manager

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `plan/` directory (empty, for future planning notes)

- [ ] **Step 1: git init**

```bash
cd /Users/shun/dev/pyxel/mon
git init
```

Expected: `Initialized empty Git repository in .../mon/.git/`

- [ ] **Step 2: Create .gitignore**

```bash
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
*.egg-info/
dist/
.DS_Store
save.json
EOF
```

- [ ] **Step 3: Initialize uv project**

```bash
uv init --no-readme
```

Expected: Creates `pyproject.toml` and `hello.py`.

- [ ] **Step 4: Delete the placeholder hello.py**

```bash
rm hello.py
```

- [ ] **Step 5: Edit pyproject.toml**

Replace the contents of `pyproject.toml` with:

```toml
[project]
name = "mon"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pyxel>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 6: Add pyxel and pytest**

```bash
uv add pyxel
uv add --dev pytest
```

Expected: `.venv/` created, `pyproject.toml` updated with resolved versions.

- [ ] **Step 7: Create directory structure and conftest.py**

```bash
mkdir -p scenes models data config assets tests plan
touch scenes/__init__.py models/__init__.py data/__init__.py config/__init__.py tests/__init__.py
```

Create `conftest.py` at project root so pytest adds the root to `sys.path` (required for `import save`):

```python
# conftest.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "chore: initialize project with uv, pyxel, pytest"
```

---

### Task 2: params.py — all tunable constants

**Files:**
- Create: `config/params.py`

- [ ] **Step 1: Write params.py**

```python
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
KEY_CONFIRM     = [13, 32]          # KEY_RETURN, KEY_SPACE
KEY_CANCEL      = [81]              # KEY_Q
KEY_MENU        = [69]              # KEY_E
KEY_MOVE_UP     = [265, 87]         # KEY_UP,    KEY_W
KEY_MOVE_DOWN   = [264, 83]         # KEY_DOWN,  KEY_S
KEY_MOVE_LEFT   = [263, 65]         # KEY_LEFT,  KEY_A
KEY_MOVE_RIGHT  = [262, 68]         # KEY_RIGHT, KEY_D
```

- [ ] **Step 2: Commit**

```bash
git add config/params.py config/__init__.py
git commit -m "feat: add config/params.py with all tunable constants"
```

---

## Chunk 2: Core Data Models

### Task 3: Move and MonsterSpec dataclasses

**Files:**
- Create: `models/monster.py`
- Create: `tests/test_monster.py`

- [ ] **Step 1: Write failing tests for stat formulas**

```python
# tests/test_monster.py
import math
from models.monster import calc_hp, calc_stat, exp_to_next


def test_calc_hp_level_1():
    # HP = floor(base * 1 / 50) + 1 + 10
    assert calc_hp(base=45, level=1) == 11  # floor(45/50) + 1 + 10 = 0 + 11


def test_calc_hp_level_10():
    # HP = floor(45 * 10 / 50) + 10 + 10 = 9 + 20 = 29
    assert calc_hp(base=45, level=10) == 29


def test_calc_stat_level_1():
    # stat = floor(50 * 1 / 50) + 5 = 1 + 5 = 6
    assert calc_stat(base=50, level=1) == 6


def test_calc_stat_level_10():
    # stat = floor(50 * 10 / 50) + 5 = 10 + 5 = 15
    assert calc_stat(base=50, level=10) == 15


def test_exp_to_next_level_1():
    # level^3 - (level-1)^3 = 1 - 0 = 1
    assert exp_to_next(1) == 1


def test_exp_to_next_level_5():
    # 5^3 - 4^3 = 125 - 64 = 61
    assert exp_to_next(5) == 61


def test_exp_to_next_level_10():
    # 10^3 - 9^3 = 1000 - 729 = 271
    assert exp_to_next(10) == 271
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_monster.py -v
```

Expected: `ModuleNotFoundError: No module named 'models.monster'`

- [ ] **Step 3: Implement monster.py**

```python
# models/monster.py
"""Monster data structures and stat calculation formulas."""
from __future__ import annotations
import math
from dataclasses import dataclass, field


def calc_hp(base: int, level: int) -> int:
    """HP = floor(base * level / 50) + level + 10"""
    return math.floor(base * level / 50) + level + 10


def calc_stat(base: int, level: int) -> int:
    """Other stats = floor(base * level / 50) + 5"""
    return math.floor(base * level / 50) + 5


def exp_to_next(level: int) -> int:
    """EXP needed to reach next level = level^3 - (level-1)^3"""
    return level ** 3 - (level - 1) ** 3


@dataclass
class Move:
    id: int
    name: str
    type: str        # e.g. "fire", "water"
    category: str    # "physical" | "special" | "status"
    power: int       # 0 for status moves
    accuracy: int    # 0–100


@dataclass
class MonsterSpec:
    """Immutable master data for a monster species."""
    id: int
    name: str
    types: list[str]              # 1 or 2 types
    base_stats: dict[str, int]    # keys: hp/atk/def/spatk/spdef/spd
    learnable_moves: list[tuple[int, int]]  # [(level, move_id), ...]
    catch_rate: int               # 1–255, higher = easier to catch


@dataclass
class Monster:
    """A player-owned monster instance."""
    spec: MonsterSpec
    level: int
    current_hp: int
    max_hp: int
    moves: list[Move]
    exp: int

    @property
    def exp_to_next(self) -> int:
        return exp_to_next(self.level)

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def get_stat(self, stat: str) -> int:
        """Return computed stat for current level."""
        if stat == "hp":
            return calc_hp(self.spec.base_stats["hp"], self.level)
        return calc_stat(self.spec.base_stats[stat], self.level)


def create_monster(spec: MonsterSpec, level: int, moves: list[Move], exp: int = 0) -> Monster:
    """Factory: build a Monster instance with correct stats for the given level."""
    hp = calc_hp(spec.base_stats["hp"], level)
    return Monster(
        spec=spec,
        level=level,
        current_hp=hp,
        max_hp=hp,
        moves=moves,
        exp=exp,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_monster.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add models/monster.py models/__init__.py tests/test_monster.py
git commit -m "feat: add Monster/MonsterSpec/Move dataclasses and stat formulas"
```

---

## Chunk 3: Type Chart, Move Data, and Battle Logic

### Task 4: Type effectiveness table

**Files:**
- Create: `data/type_chart.py`
- Create: `tests/test_type_chart.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_type_chart.py
from data.type_chart import get_effectiveness


def test_fire_vs_grass_is_super_effective():
    assert get_effectiveness("fire", "grass") == 2.0


def test_fire_vs_water_is_not_very_effective():
    assert get_effectiveness("fire", "water") == 0.5


def test_fire_vs_fire_is_not_very_effective():
    assert get_effectiveness("fire", "fire") == 0.5


def test_normal_vs_ghost_is_immune():
    assert get_effectiveness("normal", "ghost") == 0.0


def test_water_vs_ground_is_super_effective():
    assert get_effectiveness("water", "ground") == 2.0


def test_dual_type_multiplier():
    # Fire vs Grass/Bug: 2.0 * 2.0 = 4.0
    assert get_effectiveness("fire", "grass", "bug") == 4.0


def test_dual_type_cancel():
    # Water vs Fire/Rock: 2.0 * 1.0 = 2.0... wait, water vs rock is 2.0 too
    # Ground vs Fire/Flying: 2.0 * 0.0 (immune) = 0.0
    assert get_effectiveness("ground", "fire", "flying") == 0.0
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_type_chart.py -v
```

Expected: `ModuleNotFoundError: No module named 'data.type_chart'`

- [ ] **Step 3: Implement type_chart.py**

```python
# data/type_chart.py
"""Pokemon-compatible 18-type effectiveness table."""

TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy",
]

# _TABLE[attacker][defender] = multiplier
# 2.0 = super effective, 0.5 = not very effective, 0.0 = immune, 1.0 = normal
_TABLE: dict[str, dict[str, float]] = {
    "normal":   {"ghost": 0.0, "rock": 0.5, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "rock": 0.5, "dragon": 0.5,
                 "grass": 2.0, "ice": 2.0, "bug": 2.0, "steel": 2.0},
    "water":    {"water": 0.5, "grass": 0.5, "dragon": 0.5,
                 "fire": 2.0, "ground": 2.0, "rock": 2.0},
    "electric": {"electric": 0.5, "grass": 0.5, "dragon": 0.5,
                 "ground": 0.0,
                 "water": 2.0, "flying": 2.0},
    "grass":    {"fire": 0.5, "grass": 0.5, "poison": 0.5,
                 "flying": 0.5, "bug": 0.5, "dragon": 0.5, "steel": 0.5,
                 "water": 2.0, "ground": 2.0, "rock": 2.0},
    "ice":      {"water": 0.5, "ice": 0.5,
                 "grass": 2.0, "ground": 2.0, "flying": 2.0, "dragon": 2.0},
    "fighting": {"normal": 2.0, "ice": 2.0, "rock": 2.0, "dark": 2.0, "steel": 2.0,
                 "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "fairy": 0.5,
                 "ghost": 0.0},
    "poison":   {"grass": 2.0, "fairy": 2.0,
                 "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5,
                 "steel": 0.0},
    "ground":   {"fire": 2.0, "electric": 2.0, "poison": 2.0, "rock": 2.0, "steel": 2.0,
                 "grass": 0.5, "bug": 0.5,
                 "flying": 0.0},
    "flying":   {"grass": 2.0, "fighting": 2.0, "bug": 2.0,
                 "electric": 0.5, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2.0, "poison": 2.0,
                 "psychic": 0.5, "steel": 0.5,
                 "dark": 0.0},
    "bug":      {"grass": 2.0, "psychic": 2.0, "dark": 2.0,
                 "fire": 0.5, "fighting": 0.5, "flying": 0.5,
                 "poison": 0.5, "ghost": 0.5, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0,
                 "fighting": 0.5, "ground": 0.5, "steel": 0.5},
    "ghost":    {"ghost": 2.0, "psychic": 2.0,
                 "normal": 0.0, "dark": 0.5},
    "dragon":   {"dragon": 2.0,
                 "steel": 0.5,
                 "fairy": 0.0},
    "dark":     {"ghost": 2.0, "psychic": 2.0,
                 "fighting": 0.5, "dark": 0.5, "fairy": 0.5},
    "steel":    {"ice": 2.0, "rock": 2.0, "fairy": 2.0,
                 "fire": 0.5, "water": 0.5, "electric": 0.5, "steel": 0.5},
    "fairy":    {"fighting": 2.0, "dragon": 2.0, "dark": 2.0,
                 "fire": 0.5, "poison": 0.5, "steel": 0.5},
}


def get_effectiveness(attack_type: str, *defend_types: str) -> float:
    """Return combined type multiplier for an attack against one or two defender types."""
    multiplier = 1.0
    row = _TABLE.get(attack_type, {})
    for dt in defend_types:
        multiplier *= row.get(dt, 1.0)
    return multiplier
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_type_chart.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add data/type_chart.py data/__init__.py tests/test_type_chart.py
git commit -m "feat: add 18-type effectiveness table"
```

---

### Task 5: Move data (required before battle logic tests)

**Files:**
- Create: `data/moves.py`

- [ ] **Step 1: Write data/moves.py**

```python
# data/moves.py
"""All move definitions. MOVES dict is keyed by move ID."""
from models.monster import Move

MOVES: dict[int, Move] = {
    1:  Move(1,  "たいあたり",   "normal",   "physical", 40,  100),
    2:  Move(2,  "ひっかく",     "normal",   "physical", 40,  100),
    3:  Move(3,  "ひのこ",       "fire",     "special",  40,  100),
    4:  Move(4,  "みずでっぽう", "water",    "special",  40,  100),
    5:  Move(5,  "つるのムチ",   "grass",    "physical", 45,  100),
    6:  Move(6,  "かみつく",     "dark",     "physical", 60,  100),
    7:  Move(7,  "いわおとし",   "rock",     "physical", 50,   90),
    8:  Move(8,  "でんきショック","electric", "special",  40,  100),
    9:  Move(9,  "たたく",       "normal",   "physical", 40,  100),
    10: Move(10, "つばさでうつ", "flying",   "physical", 60,  100),
    11: Move(11, "どろかけ",     "ground",   "special",  55,   95),
    12: Move(12, "かぜおこし",   "flying",   "special",  40,  100),
    13: Move(13, "シャドーボール","ghost",    "special",  80,  100),
    14: Move(14, "こおりのつぶて","ice",      "physical", 40,  100),
    15: Move(15, "メタルクロー", "steel",    "physical", 50,   95),
    16: Move(16, "かえんほうしゃ","fire",     "special",  90,  100),
    17: Move(17, "なみのり",     "water",    "special",  90,  100),
    18: Move(18, "ソーラービーム","grass",    "special", 120,  100),
    19: Move(19, "10まんボルト", "electric", "special",  90,  100),
    20: Move(20, "じしん",       "ground",   "physical",100,  100),
}
```

- [ ] **Step 2: Commit**

```bash
git add data/moves.py
git commit -m "feat: add 20 moves in data/moves.py"
```

---

### Task 6: Battle logic (damage, capture, exp, level-up)

**Files:**
- Create: `models/battle.py`
- Create: `tests/test_battle_logic.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_battle_logic.py
import math
from unittest.mock import patch
from models.monster import MonsterSpec, Monster, Move, create_monster
from models.battle import calc_damage, calc_catch_probability, calc_exp_gain, apply_exp


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_spec(id=1, types=("normal",), base_stats=None, catch_rate=128) -> MonsterSpec:
    return MonsterSpec(
        id=id, name="Test",
        types=list(types),
        base_stats=base_stats or {"hp": 45, "atk": 49, "def": 49, "spatk": 65, "spdef": 65, "spd": 45},
        learnable_moves=[],
        catch_rate=catch_rate,
    )

def make_move(type="normal", category="physical", power=40, accuracy=100) -> Move:
    return Move(id=1, name="Tackle", type=type, category=category, power=power, accuracy=accuracy)

def make_monster(level=10, current_hp=None, spec=None) -> Monster:
    s = spec or make_spec()
    m = create_monster(s, level, [make_move()])
    if current_hp is not None:
        m.current_hp = current_hp
    return m


# ── Damage ───────────────────────────────────────────────────────────────────

def test_damage_uses_atk_def_for_physical():
    attacker = make_monster(level=10)
    defender = make_monster(level=10)
    move = make_move(category="physical", power=40)
    # With fixed random=1.0: damage = floor((atk/def) * power * type_eff * 1.0)
    with patch("models.battle.random_factor", return_value=1.0):
        dmg = calc_damage(attacker, defender, move)
    assert dmg >= 1


def test_damage_minimum_is_1():
    attacker = make_monster(level=1)
    defender = make_monster(level=50)
    move = make_move(power=1)
    with patch("models.battle.random_factor", return_value=0.85):
        dmg = calc_damage(attacker, defender, move)
    assert dmg == 1


def test_super_effective_doubles_damage():
    attacker = make_monster(level=10)
    defender = make_monster(level=10, spec=make_spec(types=("grass",)))
    move = make_move(type="fire", category="special", power=40)
    with patch("models.battle.random_factor", return_value=1.0):
        dmg_se = calc_damage(attacker, defender, move)
    normal_move = make_move(type="normal", category="special", power=40)
    with patch("models.battle.random_factor", return_value=1.0):
        dmg_normal = calc_damage(attacker, defender, normal_move)
    # floor(A * 2) may differ from floor(A) * 2 by at most 1
    assert abs(dmg_se - dmg_normal * 2) <= 1


# ── Capture ──────────────────────────────────────────────────────────────────

def test_catch_probability_full_hp_is_low():
    m = make_monster(level=10, spec=make_spec(catch_rate=45))
    prob = calc_catch_probability(m)
    assert 0 < prob < 0.5


def test_catch_probability_low_hp_is_high():
    m = make_monster(level=10, spec=make_spec(catch_rate=255))
    m.current_hp = 1
    prob = calc_catch_probability(m)
    assert prob > 0.9


def test_catch_probability_capped_at_0_99():
    m = make_monster(level=1, spec=make_spec(catch_rate=255))
    m.current_hp = 1
    prob = calc_catch_probability(m)
    assert prob <= 0.99


# ── Exp & Level-up ───────────────────────────────────────────────────────────

def test_exp_gain_formula():
    defeated = make_monster(level=10)
    gained = calc_exp_gain(defeated)
    assert gained == 10 * 10 * 1.0  # level * 10 * multiplier


def test_apply_exp_no_level_up():
    m = make_monster(level=5, spec=make_spec())
    initial_level = m.level
    apply_exp(m, gained=1)
    assert m.level == initial_level
    assert m.exp == 1


def test_apply_exp_triggers_level_up():
    m = make_monster(level=5)
    m.exp = 0
    # exp_to_next(5) = 5^3 - 4^3 = 125 - 64 = 61
    apply_exp(m, gained=61)
    assert m.level == 6
    assert m.max_hp > 0
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_battle_logic.py -v
```

Expected: `ModuleNotFoundError: No module named 'models.battle'` (data/moves.py already exists from Task 5)

- [ ] **Step 3: Implement battle.py**

```python
# models/battle.py
"""Pure battle logic. No Pyxel imports — fully unit-testable."""
from __future__ import annotations
import math
import random as _random
from typing import TYPE_CHECKING

from data.type_chart import get_effectiveness
from config.params import CAPTURE_BASE_MULTIPLIER, EXP_GAIN_MULTIPLIER, DAMAGE_RANDOM_MIN
from models.monster import calc_hp, calc_stat, exp_to_next

if TYPE_CHECKING:
    from models.monster import Monster, Move


def random_factor() -> float:
    """Damage roll factor in [DAMAGE_RANDOM_MIN, 1.0]. Extracted for testability."""
    return _random.uniform(DAMAGE_RANDOM_MIN, 1.0)


def calc_damage(attacker: "Monster", defender: "Monster", move: "Move") -> int:
    """Return damage dealt by attacker using move against defender."""
    if move.power == 0:
        return 0

    if move.category == "physical":
        atk = attacker.get_stat("atk")
        def_ = defender.get_stat("def")
    else:
        atk = attacker.get_stat("spatk")
        def_ = defender.get_stat("spdef")

    type_mult = get_effectiveness(move.type, *defender.spec.types)
    dmg = math.floor((atk / def_) * move.power * type_mult * random_factor())
    return max(1, dmg)


def calc_catch_probability(monster: "Monster") -> float:
    """Return probability (0–0.99) of catching monster at current HP."""
    ratio = (monster.max_hp * 3 - monster.current_hp * 2) / (monster.max_hp * 3)
    prob = ratio * (monster.spec.catch_rate / 255.0) * CAPTURE_BASE_MULTIPLIER
    return min(prob, 0.99)


def try_catch(monster: "Monster") -> bool:
    """Roll for capture. Returns True if successful."""
    return _random.random() < calc_catch_probability(monster)


def calc_exp_gain(defeated: "Monster") -> int:
    """EXP gained from defeating a monster."""
    return int(defeated.level * 10 * EXP_GAIN_MULTIPLIER)


def apply_exp(monster: "Monster", gained: int) -> list[int]:
    """Add exp to monster, trigger level-ups as needed. Returns list of levels gained."""
    from data.moves import MOVES  # local import to avoid circular
    levels_gained = []
    monster.exp += gained

    while monster.exp >= exp_to_next(monster.level):
        monster.exp -= exp_to_next(monster.level)
        old_max_hp = monster.max_hp
        monster.level += 1
        levels_gained.append(monster.level)

        # Recalculate stats
        new_max_hp = calc_hp(monster.spec.base_stats["hp"], monster.level)
        monster.current_hp += new_max_hp - old_max_hp
        monster.max_hp = new_max_hp

        # Learn moves at this level
        for (learn_level, move_id) in monster.spec.learnable_moves:
            if learn_level == monster.level and move_id in MOVES:
                new_move = MOVES[move_id]
                if len(monster.moves) < 4:
                    monster.moves.append(new_move)
                else:
                    monster.moves.pop(0)   # forget oldest
                    monster.moves.append(new_move)

    return levels_gained


def enemy_choose_move(monster: "Monster") -> "Move":
    """Enemy AI: pick a random move."""
    return _random.choice(monster.moves)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_battle_logic.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add models/battle.py tests/test_battle_logic.py
git commit -m "feat: add battle logic (damage, capture, exp, level-up)"
```

---

## Chunk 4: Monster Species Data

### Task 7: Monster species data

**Files:**
- Create: `data/monsters.py`

- [ ] **Step 1: Write data/monsters.py**

```python
# data/monsters.py
"""
All monster species and area encounter tables.
IDs 1-3: Starters (fire/water/grass). Not available as wild encounters.
IDs 4+: Wild monsters.
"""
from models.monster import MonsterSpec

MONSTERS: dict[int, MonsterSpec] = {
    # ── Starters ────────────────────────────────────────────────────────────
    1: MonsterSpec(
        id=1, name="フレアニ",
        types=["fire"],
        base_stats={"hp": 39, "atk": 52, "def": 43, "spatk": 60, "spdef": 50, "spd": 65},
        learnable_moves=[(1, 9), (4, 3), (7, 6), (10, 16)],
        catch_rate=45,
    ),
    2: MonsterSpec(
        id=2, name="アクアリ",
        types=["water"],
        base_stats={"hp": 44, "atk": 48, "def": 65, "spatk": 50, "spdef": 64, "spd": 43},
        learnable_moves=[(1, 9), (4, 4), (7, 6), (10, 17)],
        catch_rate=45,
    ),
    3: MonsterSpec(
        id=3, name="フォリア",
        types=["grass"],
        base_stats={"hp": 45, "atk": 49, "def": 49, "spatk": 65, "spdef": 65, "spd": 45},
        learnable_moves=[(1, 9), (4, 5), (7, 6), (10, 18)],
        catch_rate=45,
    ),
    # ── field_1 wild ─────────────────────────────────────────────────────────
    4: MonsterSpec(
        id=4, name="ラティク",
        types=["normal"],
        base_stats={"hp": 30, "atk": 56, "def": 35, "spatk": 25, "spdef": 35, "spd": 72},
        learnable_moves=[(1, 9), (4, 2), (8, 6)],
        catch_rate=255,
    ),
    5: MonsterSpec(
        id=5, name="バーディング",
        types=["normal", "flying"],
        base_stats={"hp": 40, "atk": 45, "def": 40, "spatk": 35, "spdef": 35, "spd": 56},
        learnable_moves=[(1, 9), (4, 12), (7, 10)],
        catch_rate=255,
    ),
    6: MonsterSpec(
        id=6, name="バグレット",
        types=["bug"],
        base_stats={"hp": 35, "atk": 30, "def": 35, "spatk": 20, "spdef": 20, "spd": 50},
        learnable_moves=[(1, 1), (5, 2)],
        catch_rate=255,
    ),
    7: MonsterSpec(
        id=7, name="シードリング",
        types=["grass"],
        base_stats={"hp": 45, "atk": 30, "def": 35, "spatk": 40, "spdef": 40, "spd": 35},
        learnable_moves=[(1, 9), (4, 5), (8, 18)],
        catch_rate=200,
    ),
    8: MonsterSpec(
        id=8, name="マドパプ",
        types=["ground"],
        base_stats={"hp": 55, "atk": 40, "def": 45, "spatk": 25, "spdef": 30, "spd": 30},
        learnable_moves=[(1, 9), (5, 11), (9, 20)],
        catch_rate=200,
    ),
    9: MonsterSpec(
        id=9, name="スパーキー",
        types=["electric"],
        base_stats={"hp": 35, "atk": 55, "def": 30, "spatk": 50, "spdef": 40, "spd": 90},
        learnable_moves=[(1, 9), (4, 8), (8, 19)],
        catch_rate=190,
    ),
    10: MonsterSpec(
        id=10, name="ペブル",
        types=["rock"],
        base_stats={"hp": 50, "atk": 60, "def": 65, "spatk": 30, "spdef": 35, "spd": 20},
        learnable_moves=[(1, 1), (5, 7)],
        catch_rate=180,
    ),
    # ── cave_1 wild ──────────────────────────────────────────────────────────
    11: MonsterSpec(
        id=11, name="バットファング",
        types=["poison", "flying"],
        base_stats={"hp": 40, "atk": 45, "def": 35, "spatk": 30, "spdef": 40, "spd": 55},
        learnable_moves=[(1, 9), (4, 12), (7, 6)],
        catch_rate=190,
    ),
    12: MonsterSpec(
        id=12, name="ロッククラッシュ",
        types=["rock", "ground"],
        base_stats={"hp": 55, "atk": 65, "def": 70, "spatk": 25, "spdef": 30, "spd": 15},
        learnable_moves=[(1, 1), (4, 7), (8, 20)],
        catch_rate=180,
    ),
    13: MonsterSpec(
        id=13, name="グール",
        types=["ghost"],
        base_stats={"hp": 30, "atk": 35, "def": 30, "spatk": 65, "spdef": 55, "spd": 45},
        learnable_moves=[(1, 9), (4, 13)],
        catch_rate=120,
    ),
    14: MonsterSpec(
        id=14, name="ダークネス",
        types=["dark"],
        base_stats={"hp": 50, "atk": 70, "def": 40, "spatk": 50, "spdef": 40, "spd": 60},
        learnable_moves=[(1, 6), (5, 13)],
        catch_rate=100,
    ),
    15: MonsterSpec(
        id=15, name="アイアンクラッド",
        types=["steel", "rock"],
        base_stats={"hp": 55, "atk": 55, "def": 85, "spatk": 30, "spdef": 55, "spd": 20},
        learnable_moves=[(1, 1), (4, 15), (8, 7)],
        catch_rate=60,
    ),
}

# ── Encounter tables ─────────────────────────────────────────────────────────
# Each entry: (monster_id, weight)
AREA_ENCOUNTER_TABLE: dict[str, list[tuple[int, int]]] = {
    "field_1": [
        (4, 40),   # ラティク     — common
        (5, 25),   # バーディング — common
        (6, 20),   # バグレット   — uncommon
        (7, 10),   # シードリング — rare
        (8,  3),   # マドパプ     — very rare
        (9,  2),   # スパーキー   — very rare
    ],
    "cave_1": [
        (11, 35),  # バットファング   — common
        (12, 30),  # ロッククラッシュ — common
        (10, 15),  # ペブル           — uncommon (also in field)
        (13, 12),  # グール           — uncommon
        (14,  6),  # ダークネス       — rare
        (15,  2),  # アイアンクラッド — very rare
    ],
}


def pick_encounter(area: str) -> MonsterSpec:
    """Weighted-random selection from area's encounter table."""
    import random
    table = AREA_ENCOUNTER_TABLE[area]
    ids, weights = zip(*table)
    (chosen_id,) = random.choices(ids, weights=weights, k=1)
    return MONSTERS[chosen_id]
```

- [ ] **Step 2: Run all tests to make sure nothing broke**

```bash
uv run pytest -v
```

Expected: all previous tests still pass.

- [ ] **Step 3: Commit**

```bash
git add data/monsters.py
git commit -m "feat: add 15 monster species and area encounter tables"
```

---

## Chunk 4: Player and Save/Load

### Task 8: Player model

**Files:**
- Create: `models/player.py`

- [ ] **Step 1: Write models/player.py**

```python
# models/player.py
"""Player state: position, party, items, current area."""
from __future__ import annotations
from dataclasses import dataclass, field
from models.monster import Monster


@dataclass
class Player:
    name: str
    area: str                          # "field_1" | "cave_1"
    pos: list[int]                     # [tile_x, tile_y]
    party: list[Monster] = field(default_factory=list)
    items: dict[str, int] = field(default_factory=lambda: {"pokeball": 5})
    caught_ids: list[int] = field(default_factory=list)

    @property
    def active_monster(self) -> Monster | None:
        return self.party[0] if self.party else None

    def add_to_party(self, monster: Monster) -> bool:
        """Add monster to party. Returns True if added, False if party full."""
        from config.params import MAX_PARTY_SIZE
        if len(self.party) >= MAX_PARTY_SIZE:
            return False
        self.party.append(monster)
        if monster.spec.id not in self.caught_ids:
            self.caught_ids.append(monster.spec.id)
        return True

    def use_item(self, item: str) -> bool:
        """Use one of the given item. Returns True if available."""
        if self.items.get(item, 0) > 0:
            self.items[item] -= 1
            return True
        return False
```

- [ ] **Step 2: Commit**

```bash
git add models/player.py
git commit -m "feat: add Player model"
```

---

### Task 9: Save/Load system

**Files:**
- Create: `save.py`
- Create: `tests/test_save.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_save.py
import json
import os
import tempfile
from unittest.mock import patch

from models.monster import create_monster
from models.player import Player
from data.monsters import MONSTERS
from data.moves import MOVES
from save import save_game, load_game


def make_player():
    spec = MONSTERS[1]
    moves = [MOVES[9], MOVES[3]]
    monster = create_monster(spec, level=5, moves=moves)
    player = Player(name="テスト", area="field_1", pos=[5, 5])
    player.party.append(monster)
    player.caught_ids = [1]
    return player


def test_save_and_load_round_trip(tmp_path):
    save_path = str(tmp_path / "save.json")
    player = make_player()
    save_game(player, path=save_path)

    loaded = load_game(path=save_path)
    assert loaded is not None
    assert loaded.name == "テスト"
    assert loaded.area == "field_1"
    assert loaded.pos == [5, 5]
    assert len(loaded.party) == 1
    assert loaded.party[0].level == 5
    assert loaded.party[0].spec.id == 1
    assert len(loaded.party[0].moves) == 2


def test_load_missing_file_returns_none(tmp_path):
    result = load_game(path=str(tmp_path / "nonexistent.json"))
    assert result is None


def test_load_corrupt_file_returns_none(tmp_path):
    corrupt = tmp_path / "save.json"
    corrupt.write_text("{ not valid json }")
    result = load_game(path=str(corrupt))
    assert result is None


def test_save_creates_file(tmp_path):
    save_path = str(tmp_path / "save.json")
    player = make_player()
    save_game(player, path=save_path)
    assert os.path.exists(save_path)
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_save.py -v
```

Expected: `ModuleNotFoundError: No module named 'save'`

- [ ] **Step 3: Implement save.py**

```python
# save.py
"""Save/load game state to/from JSON."""
from __future__ import annotations
import json
import os
from typing import Optional

from models.monster import create_monster
from models.player import Player
from data.monsters import MONSTERS
from data.moves import MOVES

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "save.json")


def save_game(player: Player, path: str = _DEFAULT_PATH) -> None:
    """Serialize player state to JSON."""
    data = {
        "player": {
            "name": player.name,
            "pos": player.pos,
            "area": player.area,
        },
        "party": [
            {
                "spec_id": m.spec.id,
                "level": m.level,
                "current_hp": m.current_hp,
                "max_hp": m.max_hp,
                "exp": m.exp,
                "move_ids": [mv.id for mv in m.moves] + [-1] * (4 - len(m.moves)),
            }
            for m in player.party
        ],
        "caught_ids": player.caught_ids,
        "items": player.items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(path: str = _DEFAULT_PATH) -> Optional[Player]:
    """Deserialize player state from JSON. Returns None if file is missing or corrupt."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        p = data["player"]
        player = Player(
            name=p["name"],
            area=p["area"],
            pos=p["pos"],
            caught_ids=data.get("caught_ids", []),
            items=data.get("items", {"pokeball": 5}),
        )
        for entry in data.get("party", []):
            spec = MONSTERS[entry["spec_id"]]
            moves = [MOVES[mid] for mid in entry["move_ids"] if mid != -1 and mid in MOVES]
            monster = create_monster(spec, entry["level"], moves, entry.get("exp", 0))
            monster.current_hp = entry["current_hp"]
            monster.max_hp = entry["max_hp"]
            player.party.append(monster)
        return player
    except Exception:
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_save.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add save.py tests/test_save.py
git commit -m "feat: add save/load system with JSON serialization"
```

---

## Chunk 5: SceneManager

### Task 10: SceneManager

**Files:**
- Create: `scene_manager.py`

- [ ] **Step 1: Write scene_manager.py**

```python
# scene_manager.py
"""Manages scene lifecycle: registration, switching, update/draw dispatch."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Scene:
    """Base class for all scenes."""
    def on_enter(self, **kwargs) -> None: pass
    def on_exit(self) -> None: pass
    def update(self) -> None: pass
    def draw(self) -> None: pass


class SceneManager:
    def __init__(self):
        self.scenes: dict[str, Scene] = {}
        self.current: Scene | None = None

    def register(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def switch(self, name: str, **kwargs) -> None:
        if self.current:
            self.current.on_exit()
        self.current = self.scenes[name]
        self.current.on_enter(**kwargs)

    def update(self) -> None:
        if self.current:
            self.current.update()

    def draw(self) -> None:
        if self.current:
            self.current.draw()
```

- [ ] **Step 2: Commit**

```bash
git add scene_manager.py
git commit -m "feat: add SceneManager with scene lifecycle"
```

---

## Chunk 6: Field Scene

### Task 11: FieldScene — map rendering, movement, camera, encounter

**Files:**
- Create: `scenes/field_scene.py`

- [ ] **Step 1: Write scenes/field_scene.py**

```python
# scenes/field_scene.py
"""Field exploration: map rendering, player movement, encounter trigger."""
from __future__ import annotations
import random
import pyxel
from scene_manager import Scene, SceneManager
from models.player import Player
from models.monster import create_monster
from data.monsters import MONSTERS, pick_encounter
from models.battle import apply_exp
from config.params import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    TILE_GRASS, TILE_BLOCK, TILE_WARP,
    ENCOUNTER_RATE, AREA_SPAWN,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT, KEY_MENU,
)
from save import save_game


AREA_MAP_BANK = {
    "field_1": 0,   # pyxres map bank index
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


class FieldScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref

    @property
    def player(self) -> Player:
        return self.player_ref[0]

    def on_enter(self, **kwargs) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self) -> None:
        self._handle_move()
        self._check_menu()

    def _any_key(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

    def _handle_move(self) -> None:
        dx, dy = 0, 0
        if self._any_key(KEY_MOVE_UP):    dy = -1
        elif self._any_key(KEY_MOVE_DOWN): dy = 1
        elif self._any_key(KEY_MOVE_LEFT): dx = -1
        elif self._any_key(KEY_MOVE_RIGHT):dx = 1
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
        return pyxel.tilemap(bank).pget(tx, ty)

    def _check_encounter(self) -> None:
        if random.random() < ENCOUNTER_RATE:
            wild_spec = pick_encounter(self.player.area)
            wild_level = max(2, (self.player.active_monster.level if self.player.active_monster else 5) + random.randint(-2, 2))
            wild_moves_ids = [ml[1] for ml in wild_spec.learnable_moves if ml[0] <= wild_level][:4] or [1]
            from data.moves import MOVES
            wild_moves = [MOVES[mid] for mid in wild_moves_ids if mid in MOVES][:4]
            if not wild_moves:
                from data.moves import MOVES
                wild_moves = [MOVES[1]]
            wild = create_monster(wild_spec, wild_level, wild_moves)
            self.sm.switch("battle", wild_monster=wild)

    def _warp(self) -> None:
        dest = AREA_WARP_DEST[self.player.area]
        key = f"from_{self.player.area}"
        spawn = AREA_SPAWN.get(dest, {}).get(key, (1, 1))
        self.player.area = dest
        self.player.pos = list(spawn)
        save_game(self.player)

    def _check_menu(self) -> None:
        if self._any_key(KEY_MENU):
            self.sm.switch("menu", return_scene="field")

    def draw(self) -> None:
        pyxel.cls(0)
        bank = AREA_MAP_BANK[self.player.area]
        # Camera: player centered, clamped to map bounds
        mw, mh = AREA_SIZE[self.player.area]
        cam_x = max(0, min(self.player.pos[0] - SCREEN_WIDTH // (2 * TILE_SIZE),
                           mw - SCREEN_WIDTH // TILE_SIZE))
        cam_y = max(0, min(self.player.pos[1] - SCREEN_HEIGHT // (2 * TILE_SIZE),
                           mh - SCREEN_HEIGHT // TILE_SIZE))
        pyxel.bltm(0, 0, bank, cam_x * TILE_SIZE, cam_y * TILE_SIZE,
                   SCREEN_WIDTH, SCREEN_HEIGHT, 0)
        # Player sprite
        sx = (self.player.pos[0] - cam_x) * TILE_SIZE
        sy = (self.player.pos[1] - cam_y) * TILE_SIZE
        pyxel.blt(sx, sy, 0, 0, 0, TILE_SIZE, TILE_SIZE, 0)
        # Area name
        area_names = {"field_1": "そうげん", "cave_1": "どうくつ"}
        name = area_names.get(self.player.area, self.player.area)
        pyxel.text(SCREEN_WIDTH - len(name) * 4 - 4, 2, name, 7)
```

- [ ] **Step 2: Commit**

```bash
git add scenes/field_scene.py scenes/__init__.py
git commit -m "feat: add FieldScene with movement, camera, and encounter trigger"
```

---

## Chunk 7: Battle Scene

### Task 12: BattleScene — UI, command handling, turn execution

**Files:**
- Create: `scenes/battle_scene.py`

- [ ] **Step 1: Write scenes/battle_scene.py**

```python
# scenes/battle_scene.py
"""Turn-based battle screen."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from models.monster import Monster
from models.player import Player
from models.battle import calc_damage, try_catch, calc_exp_gain, apply_exp, enemy_choose_move
from config.params import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    KEY_CONFIRM, KEY_CANCEL,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT,
)


# UI layout constants
_ENEMY_PANE_Y  = 0
_PLAYER_PANE_Y = 80
_CMD_PANE_Y    = 160
_MSG_PANE_Y    = 208
_PANE_H        = 80
_CMD_H         = 48
_MSG_H         = 48
_SPRITE_W      = 64
_SPRITE_H      = 64

_COMMANDS = ["たたかう", "つかまえる", "にげる", "アイテム"]
_CMD_DISABLED = {3}   # "アイテム" index — greyed out in Phase A


class BattleState:
    COMMAND   = "command"
    MOVE      = "move"
    MESSAGE   = "message"
    WIN       = "win"
    LOSE      = "lose"
    FLEE      = "flee"
    CAUGHT    = "caught"


class BattleScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self.wild: Monster | None = None

    @property
    def player(self) -> Player:
        return self.player_ref[0]
        self.state = BattleState.COMMAND
        self.cursor = 0          # command/move cursor position
        self.messages: list[str] = []
        self.msg_index = 0

    def on_enter(self, wild_monster: Monster, **kwargs) -> None:
        self.wild = wild_monster
        self.state = BattleState.COMMAND
        self.cursor = 0
        self.messages = [f"やせい の {wild_monster.spec.name} が あらわれた！"]
        self.msg_index = 0
        # Show encounter message first
        self.state = BattleState.MESSAGE
        self._pending_state = BattleState.COMMAND

    def on_exit(self) -> None:
        pass

    # ── Input helpers ─────────────────────────────────────────────────────────

    def _any(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self) -> None:
        if self.state == BattleState.MESSAGE:
            self._update_message()
        elif self.state == BattleState.COMMAND:
            self._update_command()
        elif self.state == BattleState.MOVE:
            self._update_move()
        elif self.state in (BattleState.WIN, BattleState.LOSE,
                            BattleState.FLEE, BattleState.CAUGHT):
            self._update_end()

    def _update_message(self) -> None:
        if self._any(KEY_CONFIRM):
            self.msg_index += 1
            if self.msg_index >= len(self.messages):
                self.state = self._pending_state
                self.msg_index = 0
                self.messages = []

    def _update_command(self) -> None:
        if self._any(KEY_MOVE_UP):    self.cursor = (self.cursor - 2) % 4
        elif self._any(KEY_MOVE_DOWN): self.cursor = (self.cursor + 2) % 4
        elif self._any(KEY_MOVE_LEFT): self.cursor = self.cursor - 1 if self.cursor % 2 else self.cursor
        elif self._any(KEY_MOVE_RIGHT):self.cursor = self.cursor + 1 if self.cursor % 2 == 0 else self.cursor

        if self._any(KEY_CONFIRM):
            if self.cursor in _CMD_DISABLED:
                self._show_messages(["アイテムがない！"], BattleState.COMMAND)
                return
            if self.cursor == 0:   # たたかう
                self.state = BattleState.MOVE
                self.cursor = 0
            elif self.cursor == 1: # つかまえる
                self._do_catch()
            elif self.cursor == 2: # にげる
                self._show_messages(["にげた！"], BattleState.FLEE)

    def _update_move(self) -> None:
        player_mon = self.player.active_monster
        moves = player_mon.moves if player_mon else []
        n = len(moves)
        if self._any(KEY_MOVE_UP):    self.cursor = max(0, self.cursor - 1)
        elif self._any(KEY_MOVE_DOWN): self.cursor = min(n - 1, self.cursor + 1)
        elif self._any(KEY_CANCEL):
            self.state = BattleState.COMMAND
            self.cursor = 0
            return
        if self._any(KEY_CONFIRM):
            self._do_attack(moves[self.cursor])

    def _update_end(self) -> None:
        if self._any(KEY_CONFIRM):
            if self.state in (BattleState.WIN, BattleState.LOSE, BattleState.FLEE):
                if self.state == BattleState.LOSE:
                    if self.player.active_monster:
                        self.player.active_monster.current_hp = 1
                self.sm.switch("field")
            elif self.state == BattleState.CAUGHT:
                if self.wild:
                    self.player.add_to_party(self.wild)
                self.sm.switch("field")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _do_attack(self, move) -> None:
        player_mon = self.player.active_monster
        msgs = []
        # Player attacks
        dmg = calc_damage(player_mon, self.wild, move)
        self.wild.current_hp = max(0, self.wild.current_hp - dmg)
        msgs.append(f"{player_mon.spec.name} の {move.name}！")
        msgs.append(f"{self.wild.spec.name} に {dmg} ダメージ！")

        if self.wild.is_fainted:
            exp = calc_exp_gain(self.wild)
            levels = apply_exp(player_mon, exp)
            msgs.append(f"てきの {self.wild.spec.name} を たおした！")
            msgs.append(f"{player_mon.spec.name} は {exp} けいけんちを えた！")
            for lv in levels:
                msgs.append(f"{player_mon.spec.name} は Lv{lv} に なった！")
            self._show_messages(msgs, BattleState.WIN)
            return

        # Enemy attacks
        enemy_move = enemy_choose_move(self.wild)
        edm = calc_damage(self.wild, player_mon, enemy_move)
        player_mon.current_hp = max(0, player_mon.current_hp - edm)
        msgs.append(f"てきの {self.wild.spec.name} の {enemy_move.name}！")
        msgs.append(f"{player_mon.spec.name} に {edm} ダメージ！")

        if player_mon.is_fainted:
            msgs.append(f"{player_mon.spec.name} は たおれた…")
            self._show_messages(msgs, BattleState.LOSE)
        else:
            self._show_messages(msgs, BattleState.COMMAND)

    def _do_catch(self) -> None:
        if not self.player.use_item("pokeball"):
            self._show_messages(["モンスターボールがない！"], BattleState.COMMAND)
            return
        if try_catch(self.wild):
            self._show_messages(
                [f"モンスターボールを なげた！", f"{self.wild.spec.name} を つかまえた！"],
                BattleState.CAUGHT,
            )
        else:
            self._show_messages(
                ["モンスターボールを なげた！", "だがうまくいかなかった…"],
                BattleState.COMMAND,
            )

    def _show_messages(self, msgs: list[str], next_state: str) -> None:
        self.messages = msgs
        self.msg_index = 0
        self._pending_state = next_state
        self.state = BattleState.MESSAGE

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self) -> None:
        pyxel.cls(0)
        self._draw_enemy_pane()
        self._draw_player_pane()
        if self.state == BattleState.COMMAND:
            self._draw_command_menu()
        elif self.state == BattleState.MOVE:
            self._draw_move_menu()
        else:
            self._draw_message_box()

    def _draw_hp_bar(self, x: int, y: int, current: int, max_hp: int, width: int = 64) -> None:
        ratio = current / max_hp if max_hp > 0 else 0
        filled = int(width * ratio)
        pyxel.rect(x, y, width, 4, 1)
        color = 11 if ratio > 0.5 else (10 if ratio > 0.25 else 8)
        if filled > 0:
            pyxel.rect(x, y, filled, 4, color)

    def _draw_enemy_pane(self) -> None:
        pyxel.rect(0, _ENEMY_PANE_Y, SCREEN_WIDTH, _PANE_H, 5)
        if self.wild:
            # Sprite placeholder (white box until .pyxres is made)
            pyxel.rectb(8, _ENEMY_PANE_Y + 8, _SPRITE_W, _SPRITE_H, 7)
            pyxel.text(8, _ENEMY_PANE_Y + 2, self.wild.spec.name, 7)
            pyxel.text(160, _ENEMY_PANE_Y + 2, f"Lv{self.wild.level}", 7)
            self._draw_hp_bar(160, _ENEMY_PANE_Y + 12, self.wild.current_hp, self.wild.max_hp)
            pyxel.text(160, _ENEMY_PANE_Y + 18, f"{self.wild.current_hp}/{self.wild.max_hp}", 7)

    def _draw_player_pane(self) -> None:
        pyxel.rect(0, _PLAYER_PANE_Y, SCREEN_WIDTH, _PANE_H, 1)
        mon = self.player.active_monster
        if mon:
            pyxel.rectb(160, _PLAYER_PANE_Y + 8, _SPRITE_W, _SPRITE_H, 7)
            pyxel.text(8, _PLAYER_PANE_Y + 2, mon.spec.name, 7)
            pyxel.text(8, _PLAYER_PANE_Y + 10, f"Lv{mon.level}", 7)
            self._draw_hp_bar(8, _PLAYER_PANE_Y + 20, mon.current_hp, mon.max_hp)
            pyxel.text(8, _PLAYER_PANE_Y + 26, f"{mon.current_hp}/{mon.max_hp}", 7)

    def _draw_command_menu(self) -> None:
        pyxel.rect(0, _CMD_PANE_Y, SCREEN_WIDTH, _CMD_H, 2)
        for i, cmd in enumerate(_COMMANDS):
            col = (i % 2) * (SCREEN_WIDTH // 2)
            row = (i // 2) * 16
            color = 13 if i in _CMD_DISABLED else 7
            prefix = ">" if i == self.cursor else " "
            pyxel.text(col + 8, _CMD_PANE_Y + 8 + row, f"{prefix}{cmd}", color)

    def _draw_move_menu(self) -> None:
        mon = self.player.active_monster
        pyxel.rect(0, _CMD_PANE_Y, SCREEN_WIDTH, _CMD_H, 2)
        if not mon:
            return
        for i, move in enumerate(mon.moves):
            prefix = ">" if i == self.cursor else " "
            pyxel.text(8, _CMD_PANE_Y + 8 + i * 10, f"{prefix}{move.name}", 7)

    def _draw_message_box(self) -> None:
        pyxel.rect(0, _MSG_PANE_Y, SCREEN_WIDTH, _MSG_H, 1)
        pyxel.rectb(0, _MSG_PANE_Y, SCREEN_WIDTH, _MSG_H, 7)
        if self.messages and self.msg_index < len(self.messages):
            pyxel.text(8, _MSG_PANE_Y + 8, self.messages[self.msg_index], 7)
        if self.msg_index < len(self.messages) - 1 or self.state not in (
            BattleState.WIN, BattleState.LOSE, BattleState.FLEE, BattleState.CAUGHT
        ):
            pyxel.text(SCREEN_WIDTH - 12, _MSG_PANE_Y + _MSG_H - 10, "▼", 7)
```

- [ ] **Step 2: Commit**

```bash
git add scenes/battle_scene.py
git commit -m "feat: add BattleScene with command/move selection and turn execution"
```

---

## Chunk 8: Title and Menu Scenes

### Task 13: TitleScene

**Files:**
- Create: `scenes/title_scene.py`

- [ ] **Step 1: Write scenes/title_scene.py**

```python
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
from config.params import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_CONFIRM, KEY_CANCEL, KEY_MOVE_UP, KEY_MOVE_DOWN


_STARTERS = [1, 2, 3]   # monster IDs for starter selection
_STARTER_TYPES = ["ほのお", "みず", "くさ"]

# Input: hiragana rows for name entry (simplified)
_KANA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん") + ["けってい"]
_KANA_DONE = "けってい"


class TitlePhase:
    SPLASH   = "splash"
    CHOICE   = "choice"     # continue / new game
    NAME     = "name"       # name input
    STARTER  = "starter"    # pick starter


class TitleScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        """player_ref is a 1-element list so FieldScene/BattleScene share the same Player."""
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
                if self.cursor == 0:  # つづきから
                    player = load_game()
                    self.player_ref[0] = player
                    self.sm.switch("field")
                else:                 # はじめから
                    self.phase = TitlePhase.NAME
                    self.cursor = 0

        elif self.phase == TitlePhase.NAME:
            if self._any(KEY_MOVE_LEFT):  self.kana_cursor = max(0, self.kana_cursor - 1)
            if self._any(KEY_MOVE_RIGHT): self.kana_cursor = min(len(_KANA) - 1, self.kana_cursor + 1)
            if self._any(KEY_CONFIRM):
                selected = _KANA[self.kana_cursor]
                if selected == _KANA_DONE:
                    if self.player_name:  # transition only if name is non-empty
                        self.phase = TitlePhase.STARTER
                        self.cursor = 0
                elif len(self.player_name) < 8:
                    self.player_name += selected
            if self._any(KEY_CANCEL):
                if self.player_name:
                    self.player_name = self.player_name[:-1]

        elif self.phase == TitlePhase.STARTER:
            if self._any(KEY_MOVE_LEFT):  self.cursor = (self.cursor - 1) % 3
            if self._any(KEY_MOVE_RIGHT): self.cursor = (self.cursor + 1) % 3
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
            pyxel.text(SCREEN_WIDTH // 2 - 20, 80, "MON", 10)
            pyxel.text(SCREEN_WIDTH // 2 - 36, 100, "Press Enter", 7)

        elif self.phase == TitlePhase.CHOICE:
            pyxel.text(80, 80, (">" if self.cursor == 0 else " ") + "つづきから", 7)
            pyxel.text(80, 96, (">" if self.cursor == 1 else " ") + "はじめから", 7)

        elif self.phase == TitlePhase.NAME:
            pyxel.text(8, 8, "なまえを いれてね", 7)
            pyxel.text(8, 24, self.player_name + "_", 10)
            # Kana picker — show a sliding window of 20 chars
            start = max(0, self.kana_cursor - 10)
            for i, ch in enumerate(_KANA[start:start + 20]):
                color = 10 if (start + i) == self.kana_cursor else 7
                pyxel.text(8 + i * 12, 48, ch, color)
            pyxel.text(8, 64, "Enter:かくてい  Q:けす", 13)

        elif self.phase == TitlePhase.STARTER:
            pyxel.text(40, 8, "さいしょの モンスターを えらんで！", 7)
            for i, (sid, stype) in enumerate(zip(_STARTERS, _STARTER_TYPES)):
                spec = MONSTERS[sid]
                x = 16 + i * 80
                color = 10 if i == self.cursor else 7
                prefix = "▶" if i == self.cursor else " "
                pyxel.text(x, 80, prefix + spec.name, color)
                pyxel.text(x + 4, 92, stype, 13)
```

- [ ] **Step 2: Commit**

```bash
git add scenes/title_scene.py
git commit -m "feat: add TitleScene with splash, continue/new, name input, starter pick"
```

---

### Task 14: MenuScene

**Files:**
- Create: `scenes/menu_scene.py`

- [ ] **Step 1: Write scenes/menu_scene.py**

```python
# scenes/menu_scene.py
"""In-game menu: party, Pokedex, bag, save."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from models.player import Player
from data.monsters import MONSTERS
from save import save_game
from config.params import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_CONFIRM, KEY_CANCEL, KEY_MOVE_UP, KEY_MOVE_DOWN


_MAIN_ITEMS = ["てもち", "ずかん", "バッグ", "セーブ", "もどる"]


class MenuPhase:
    MAIN   = "main"
    PARTY  = "party"
    DEX    = "dex"
    BAG    = "bag"
    SAVING = "saving"


class MenuScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self.return_scene = "field"

    @property
    def player(self) -> Player:
        return self.player_ref[0]
        self.phase = MenuPhase.MAIN
        self.cursor = 0
        self.save_msg = ""
        self.save_msg_timer = 0

    def on_enter(self, return_scene: str = "field", **kwargs) -> None:
        self.return_scene = return_scene
        self.phase = MenuPhase.MAIN
        self.cursor = 0

    def on_exit(self) -> None:
        pass

    def _any(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

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
        if self._any(KEY_MOVE_UP):    self.cursor = (self.cursor - 1) % n
        elif self._any(KEY_MOVE_DOWN): self.cursor = (self.cursor + 1) % n
        elif self._any(KEY_CANCEL):
            self.sm.switch(self.return_scene)
        elif self._any(KEY_CONFIRM):
            if self.cursor == 0:   self.phase = MenuPhase.PARTY
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
        if self.phase == MenuPhase.MAIN:
            self._draw_main()
        elif self.phase == MenuPhase.PARTY:
            self._draw_party()
        elif self.phase == MenuPhase.DEX:
            self._draw_dex()
        elif self.phase == MenuPhase.BAG:
            self._draw_bag()

    def _draw_main(self) -> None:
        pyxel.text(8, 8, "メニュー", 7)
        for i, item in enumerate(_MAIN_ITEMS):
            prefix = ">" if i == self.cursor else " "
            pyxel.text(16, 24 + i * 12, prefix + item, 7)
        if self.save_msg_timer > 0:
            pyxel.text(8, SCREEN_HEIGHT - 12, self.save_msg, 10)

    def _draw_party(self) -> None:
        pyxel.text(8, 8, "てもち", 7)
        for i, mon in enumerate(self.player.party):
            y = 24 + i * 20
            pyxel.text(8,  y, mon.spec.name, 7)
            pyxel.text(8,  y + 8, f"Lv{mon.level}  HP{mon.current_hp}/{mon.max_hp}", 13)

    def _draw_dex(self) -> None:
        pyxel.text(8, 8, "ずかん", 7)
        pyxel.text(8, 20, f"つかまえた: {len(self.player.caught_ids)}ひき", 7)
        for i, mid in enumerate(sorted(self.player.caught_ids)):
            if mid in MONSTERS:
                pyxel.text(8, 32 + i * 10, f"No.{mid:03d} {MONSTERS[mid].name}", 7)

    def _draw_bag(self) -> None:
        pyxel.text(8, 8, "バッグ", 7)
        y = 24
        for item, count in self.player.items.items():
            name = "モンスターボール" if item == "pokeball" else item
            pyxel.text(8, y, f"{name} x{count}", 7)
            y += 12
```

- [ ] **Step 2: Commit**

```bash
git add scenes/menu_scene.py
git commit -m "feat: add MenuScene with party/dex/bag/save views"
```

---

## Chunk 9: main.py — Wiring Everything Together

### Task 15: main.py

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write main.py**

```python
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

    # Shared player reference so all scenes stay in sync.
    # TitleScene sets player_ref[0] on new game or load.
    player_ref: list[Player | None] = [None]

    # All scenes share player_ref so TitleScene can set the Player and
    # FieldScene/BattleScene/MenuScene pick it up via their .player property.
    title   = TitleScene(sm, player_ref)   # TitleScene sets player_ref[0]
    field   = FieldScene(sm, player_ref)   # reads player_ref[0] via .player
    battle  = BattleScene(sm, player_ref)  # reads player_ref[0] via .player
    menu    = MenuScene(sm, player_ref)    # reads player_ref[0] via .player

    sm.register("title",  title)
    sm.register("field",  field)
    sm.register("battle", battle)
    sm.register("menu",   menu)

    sm.switch("title")

    pyxel.run(sm.update, sm.draw)


if __name__ == "__main__":
    main()
```

> **Note:** `FieldScene`, `BattleScene`, and `MenuScene` need to accept `player_ref: list` instead of `Player` directly so they pick up the player set by `TitleScene`. Update their constructors to use `self.player_ref = player_ref` and replace `self.player` with `self.player_ref[0]` throughout each scene.

- [ ] **Step 2: Create placeholder assets/game.pyxres**

The `.pyxres` file must be created with the Pyxel editor (the `pyxel.save()` API requires a running game loop and cannot be scripted from the command line).

```bash
uv run pyxel edit assets/game.pyxres
```

This opens the Pyxel editor. Save an empty file immediately (Ctrl+S), then close. This creates a valid `.pyxres` that `pyxel.load()` can read. Full tile/sprite work is a separate step after the game boots.

> **Note:** Walk animation (2-frame) is intentionally deferred — the player sprite in FieldScene draws a static tile until the `.pyxres` asset is complete. Add animation in a separate pass after the tileset is drawn.

- [ ] **Step 3: Run full test suite one final time**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add main.py assets/game.pyxres
git commit -m "feat: wire all scenes in main.py, add placeholder .pyxres asset"
```

---

## Next Steps (after Phase A is running)

1. **Draw assets** — open `uv run pyxel edit assets/game.pyxres` and draw:
   - Player sprite (tile 0,0 in image bank 0)
   - Monster sprites (one per species)
   - Tile sheet: tiles 0–15 (walkable), 16–19 (grass), 32–63 (block), 64–67 (warp)
   - Maps in map banks 0 (field_1) and 1 (cave_1)

2. **Add BGM/SFX** — in pyxes editor, create sounds for battle start, level-up, capture

3. **Playtest balance** — adjust `config/params.py` values: `ENCOUNTER_RATE`, monster `catch_rate`, `EXP_GAIN_MULTIPLIER`

4. **Phase B planning** — towns, NPCs, gym boss → new spec + plan
