# tests/test_save.py
import os
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
