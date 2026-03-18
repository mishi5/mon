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
                    monster.moves.pop(0)   # forget oldest (intentional simplification)
                    monster.moves.append(new_move)

    return levels_gained


def enemy_choose_move(monster: "Monster") -> "Move":
    """Enemy AI: pick a random move."""
    return _random.choice(monster.moves)
