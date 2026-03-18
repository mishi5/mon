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
