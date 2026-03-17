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
