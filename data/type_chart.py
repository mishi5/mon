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
