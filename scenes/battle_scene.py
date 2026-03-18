# scenes/battle_scene.py
"""Turn-based battle screen."""
from __future__ import annotations
import pyxel
from scene_manager import Scene, SceneManager
from gfx import jtext
from models.monster import Monster
from models.player import Player
from models.battle import calc_damage, try_catch, calc_exp_gain, apply_exp, enemy_choose_move
from config.params import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    KEY_CONFIRM, KEY_CANCEL,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT,
)

# UI layout
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
_CMD_DISABLED = {3}   # "アイテム" greyed out in Phase A


class BattleState:
    COMMAND = "command"
    MOVE    = "move"
    MESSAGE = "message"
    WIN     = "win"
    LOSE    = "lose"
    FLEE    = "flee"
    CAUGHT  = "caught"


class BattleScene(Scene):
    def __init__(self, sm: SceneManager, player_ref: list):
        self.sm = sm
        self.player_ref = player_ref
        self.wild: Monster | None = None
        self.state = BattleState.COMMAND
        self.cursor = 0
        self.messages: list[str] = []
        self.msg_index = 0
        self._pending_state = BattleState.COMMAND

    @property
    def player(self) -> Player:
        return self.player_ref[0]

    def on_enter(self, wild_monster: Monster, **kwargs) -> None:
        self.wild = wild_monster
        self.cursor = 0
        self.messages = [f"やせいの {wild_monster.spec.name} が あらわれた！"]
        self.msg_index = 0
        self._pending_state = BattleState.COMMAND
        self.state = BattleState.MESSAGE

    def on_exit(self) -> None:
        pass

    def _any(self, keys: list[int]) -> bool:
        return any(pyxel.btnp(k) for k in keys)

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
        if self._any(KEY_MOVE_UP):     self.cursor = (self.cursor - 2) % 4
        elif self._any(KEY_MOVE_DOWN): self.cursor = (self.cursor + 2) % 4
        elif self._any(KEY_MOVE_LEFT):
            if self.cursor % 2 == 1: self.cursor -= 1
        elif self._any(KEY_MOVE_RIGHT):
            if self.cursor % 2 == 0: self.cursor += 1

        if self._any(KEY_CONFIRM):
            if self.cursor in _CMD_DISABLED:
                self._show_messages(["アイテムがない！"], BattleState.COMMAND)
            elif self.cursor == 0:   # たたかう
                self.state = BattleState.MOVE
                self.cursor = 0
            elif self.cursor == 1:   # つかまえる
                self._do_catch()
            elif self.cursor == 2:   # にげる
                self._show_messages(["にげた！"], BattleState.FLEE)

    def _update_move(self) -> None:
        player_mon = self.player.active_monster
        moves = player_mon.moves if player_mon else []
        n = len(moves)
        if self._any(KEY_MOVE_UP):     self.cursor = max(0, self.cursor - 1)
        elif self._any(KEY_MOVE_DOWN): self.cursor = min(n - 1, self.cursor + 1)
        elif self._any(KEY_CANCEL):
            self.state = BattleState.COMMAND
            self.cursor = 0
            return
        if self._any(KEY_CONFIRM) and moves:
            self._do_attack(moves[self.cursor])

    def _update_end(self) -> None:
        if self._any(KEY_CONFIRM):
            if self.state == BattleState.LOSE:
                if self.player.active_monster:
                    self.player.active_monster.current_hp = 1
            if self.state == BattleState.CAUGHT and self.wild:
                self.player.add_to_party(self.wild)
            self.sm.switch("field")

    def _do_attack(self, move) -> None:
        player_mon = self.player.active_monster
        msgs = []
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
                ["モンスターボールを なげた！", f"{self.wild.spec.name} を つかまえた！"],
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
            pyxel.rectb(8, _ENEMY_PANE_Y + 8, _SPRITE_W, _SPRITE_H, 7)
            jtext(8,   _ENEMY_PANE_Y + 2, self.wild.spec.name, 7)
            jtext(160, _ENEMY_PANE_Y + 2, f"Lv{self.wild.level}", 7)
            self._draw_hp_bar(160, _ENEMY_PANE_Y + 12, self.wild.current_hp, self.wild.max_hp)
            jtext(160, _ENEMY_PANE_Y + 18,
                       f"{self.wild.current_hp}/{self.wild.max_hp}", 7)

    def _draw_player_pane(self) -> None:
        pyxel.rect(0, _PLAYER_PANE_Y, SCREEN_WIDTH, _PANE_H, 1)
        mon = self.player.active_monster
        if mon:
            pyxel.rectb(160, _PLAYER_PANE_Y + 8, _SPRITE_W, _SPRITE_H, 7)
            jtext(8, _PLAYER_PANE_Y + 2,  mon.spec.name, 7)
            jtext(8, _PLAYER_PANE_Y + 10, f"Lv{mon.level}", 7)
            self._draw_hp_bar(8, _PLAYER_PANE_Y + 20, mon.current_hp, mon.max_hp)
            jtext(8, _PLAYER_PANE_Y + 26,
                       f"{mon.current_hp}/{mon.max_hp}", 7)

    def _draw_command_menu(self) -> None:
        pyxel.rect(0, _CMD_PANE_Y, SCREEN_WIDTH, _CMD_H, 2)
        for i, cmd in enumerate(_COMMANDS):
            col = (i % 2) * (SCREEN_WIDTH // 2)
            row = (i // 2) * 16
            color = 13 if i in _CMD_DISABLED else 7
            prefix = ">" if i == self.cursor else " "
            jtext(col + 8, _CMD_PANE_Y + 8 + row, f"{prefix}{cmd}", color)

    def _draw_move_menu(self) -> None:
        mon = self.player.active_monster
        pyxel.rect(0, _CMD_PANE_Y, SCREEN_WIDTH, _CMD_H, 2)
        if not mon:
            return
        for i, move in enumerate(mon.moves):
            prefix = ">" if i == self.cursor else " "
            jtext(8, _CMD_PANE_Y + 8 + i * 12, f"{prefix}{move.name}", 7)

    def _draw_message_box(self) -> None:
        pyxel.rect(0, _MSG_PANE_Y, SCREEN_WIDTH, _MSG_H, 1)
        pyxel.rectb(0, _MSG_PANE_Y, SCREEN_WIDTH, _MSG_H, 7)
        if self.messages and self.msg_index < len(self.messages):
            jtext(8, _MSG_PANE_Y + 8, self.messages[self.msg_index], 7)
        # Show advance indicator unless on last message of a terminal state
        at_last = self.msg_index >= len(self.messages) - 1
        terminal = self.state in (BattleState.WIN, BattleState.LOSE,
                                  BattleState.FLEE, BattleState.CAUGHT)
        if not (at_last and terminal):
            jtext(SCREEN_WIDTH - 12, _MSG_PANE_Y + _MSG_H - 10, "v", 7)
