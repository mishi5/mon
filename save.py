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
