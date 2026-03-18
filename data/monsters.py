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
AREA_ENCOUNTER_TABLE: dict[str, list[tuple[int, int]]] = {
    "field_1": [
        (4, 40), (5, 25), (6, 20), (7, 10), (8, 3), (9, 2),
    ],
    "cave_1": [
        (11, 35), (12, 30), (10, 15), (13, 12), (14, 6), (15, 2),
    ],
}


def pick_encounter(area: str) -> MonsterSpec:
    """Weighted-random selection from area's encounter table."""
    import random
    table = AREA_ENCOUNTER_TABLE[area]
    ids, weights = zip(*table)
    (chosen_id,) = random.choices(ids, weights=weights, k=1)
    return MONSTERS[chosen_id]
