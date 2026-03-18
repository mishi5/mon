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
    assert gained == 10 * 10 * 1  # level * 10 * multiplier


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
