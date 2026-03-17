# Monster RPG (ゲームボーイテイスト) 設計仕様

**日付:** 2026-03-17
**エンジン:** Pyxel
**フェーズ:** Phase A（基本サイクル） → Phase B（町・ストーリー追加）

---

## 概要

ポケモン赤緑に着想を得たゲームボーイテイストのモンスター収集RPG。フィールド探索・野生モンスターとのエンカウント・ターン制バトル・モンスター捕獲の基本サイクルをPhase Aとして実装する。

---

## Phase A スコープ

- フィールド探索（2エリア：草原 + 洞窟）
- 草むらでの野生モンスターランダムエンカウント
- ターン制バトル（たたかう / つかまえる / にげる / アイテム）
- モンスター捕獲
- JSONセーブ/ロード
- タイトル画面・新規ゲーム開始フロー

**Phase Aの簡略化方針（明示的なスコープ外）:**
- PPシステムなし（技は使用回数制限なし）
- 逃げるは常に成功
- アイテムはモンスターボールのみ（回復アイテムは Phase B）
- 複数セーブスロットなし

Phase Bで追加予定（別スペック）：1〜2つの町、NPC会話、ストーリー、ジム風ボス、回復アイテム

---

## アーキテクチャ

### ディレクトリ構成

```
mon/
├── main.py                  # エントリーポイント、Pyxel初期化
├── scene_manager.py         # シーン切り替え管理
├── scenes/
│   ├── title_scene.py       # タイトル画面
│   ├── field_scene.py       # フィールド探索
│   ├── battle_scene.py      # バトル画面
│   └── menu_scene.py        # メニュー画面
├── models/
│   ├── monster.py           # Monsterクラス（インスタンス）
│   ├── player.py            # Playerクラス
│   └── battle.py            # バトルロジック
├── data/
│   ├── monsters.py          # モンスターマスターデータ（15〜25匹）
│   ├── moves.py             # 技データ
│   └── type_chart.py        # タイプ相性テーブル
├── config/
│   └── params.py            # ゲームパラメータ（調整用）
├── assets/
│   └── game.pyxres          # スプライト・マップ・BGMデータ
└── pyproject.toml
```

### SceneManager

```python
class SceneManager:
    def __init__(self):
        self.scenes = {}      # name -> Scene
        self.current = None

    def switch(self, name, **kwargs):
        if self.current:
            self.current.on_exit()
        self.current = self.scenes[name]
        self.current.on_enter(**kwargs)

    def update(self): self.current.update()
    def draw(self):   self.current.draw()
```

各シーンは `update()` / `draw()` / `on_enter(**kwargs)` / `on_exit()` を実装する。

**シーン登録:** `main.py` の起動時に全シーンを `SceneManager.scenes` に登録する。

```python
# main.py
sm = SceneManager()
sm.scenes["title"]  = TitleScene(sm)
sm.scenes["field"]  = FieldScene(sm)
sm.scenes["battle"] = BattleScene(sm)
sm.scenes["menu"]   = MenuScene(sm)
sm.switch("title")
```

**シーン間インターフェース（kwargs契約）:**

| シーン | on_enter の引数 |
|---|---|
| `title_scene` | なし |
| `field_scene` | なし（セーブデータからPlayerを復元済み） |
| `battle_scene` | `wild_monster: Monster`（エンカウントした野生モンスター） |
| `menu_scene` | `return_scene: str`（メニューを閉じた後に戻るシーン名） |

---

## モンスターシステム

### データ構造

```python
@dataclass
class MonsterSpec:  # マスターデータ（不変）
    id: int
    name: str
    types: list[str]              # 例: ["fire"], ["water", "flying"]
    base_stats: dict              # hp/atk/def/spatk/spdef/spd (各 1〜255)
    learnable_moves: list[tuple]  # [(level, move_id), ...] レベルアップで覚える技
    catch_rate: int               # 捕獲しやすさ (1-255、高いほど捕まりやすい)

@dataclass
class Move:
    id: int
    name: str
    type: str       # タイプ名 例: "fire"
    category: str   # "physical" | "special" | "status"
    power: int      # 威力 (0 = 変化技)
    accuracy: int   # 命中率 (0-100)

@dataclass
class Monster:      # プレイヤーが所持するインスタンス
    spec: MonsterSpec
    level: int
    current_hp: int
    max_hp: int        # 算出済みの最大HP（レベルアップ時に再計算）
    moves: list[Move]  # 最大4つ
    exp: int           # 現在の経験値
    # exp_to_next は level から毎回算出する導出値。保存しない。
    # exp_to_next(level) = level^3 - (level-1)^3
```

### ステータス計算式

```
HP    = floor(base_hp * level / 50) + level + 10
その他 = floor(base_stat * level / 50) + 5
```

レベルアップ時に全ステータスを再計算する。HPの増加分だけ `current_hp` にも加算する。

### 経験値・レベルアップ

```
exp_to_next(level) = level^3 - (level-1)^3   # 例: Lv5→6 = 125-64 = 61
```

野生モンスターを倒すと獲得経験値 = `倒した敵のレベル × 10 × EXP_GAIN_MULTIPLIER`。
`exp >= exp_to_next` になるとレベルアップ。レベルアップ時に `learnable_moves` を確認し、
該当レベルの技を覚える。

**設計上の決定（意図的な簡略化）:** 4技を超える場合はリストの先頭（最も古い技）を自動的に忘れる。
ポケモンのような「どの技を忘れるか選択」UIは Phase A では実装しない。

### ダメージ計算

```
攻撃側ステータス = 物理技 → atk、特殊技 → spatk
防御側ステータス = 物理技 → def、特殊技 → spdef

ダメージ = floor((攻撃 / 防御) × 技の威力 × タイプ相性 × 乱数(0.85〜1.0))
最小ダメージ = 1
```

### タイプ相性

18タイプ×18タイプの2D辞書テーブル（ポケモン準拠）。値は `2.0` / `1.0` / `0.5` / `0.0`。

### 捕獲判定

```
catch_probability = (max_hp * 3 - current_hp * 2) / (max_hp * 3) * (catch_rate / 255.0)
捕獲成否 = random() < catch_probability
```

単発ロール（シェイクアニメーションは演出のみで判定には無関係）。
`catch_probability` は `min(catch_probability, 0.99)` で上限を設ける（100%捕獲なし）。

---

## バトルシステム

### Phase A バトルの前提

- バトルに参加するのは **手持ち先頭の1匹のみ**（交代なし）
- 手持ち1匹がHPゼロになった場合はそのままバトル終了（全滅扱い）
- 全滅時はフィールドの現在位置でHP=1の状態で復帰（ゲームオーバーなし）

### バトルの流れ

1. プレイヤーのコマンドを選択（たたかう / つかまえる / にげる / アイテム）
2. 素早さ比較で行動順を決定
   - 素早さが同値の場合は 50% の確率でプレイヤー先攻
3. 行動実行（下記参照）
4. 敵が倒れた → バトル終了（経験値獲得）
5. 自モンスターが倒れた → バトル終了（フィールドに戻る、HP=1で復帰）
6. 1〜5 を繰り返す

### コマンド詳細

| コマンド | 動作 |
|---|---|
| **たたかう** | 技を選択 → ダメージ計算 → 敵ターン |
| **つかまえる** | モンスターボールを1つ消費して捕獲ロール → 成功/失敗メッセージ → **敵ターンなし** |
| **にげる** | 常に成功。フィールドに戻る。**敵ターンなし** |
| **アイテム** | Phase A では使用不可（「アイテムがない」メッセージを表示）。捕獲は「つかまえる」コマンド専用 |

**設計上の決定:** 「つかまえる」は独立コマンドとし、「アイテム」コマンドは Phase A では無効化する。コマンドスロットは4つ確保するが、「アイテム」は選択不可のグレーアウト表示にする。

敵の行動：所持技からランダム選択。

---

## フィールドシステム

### マップ

Pyxelマップエディタで `.pyxres` ファイルに作成。

**タイル番号（`game.pyxres` 作成時にこれに合わせる）:**

```python
# config/params.py
TILE_WALKABLE = list(range(0, 16))    # 0〜15: 草地・道など
TILE_GRASS    = list(range(16, 20))   # 16〜19: 草むら（エンカウント発生）
TILE_BLOCK    = list(range(32, 64))   # 32〜63: 壁・木・水など（通行不可）
TILE_WARP     = list(range(64, 68))   # 64〜67: エリア遷移トリガー
```

これらの値は `.pyxres` 制作時に確定させる。

### エリア構成と遷移

```
field_1（草原）
  - サイズ: 32×32タイル（512×512ピクセル相当）
  - プレイヤー初期スポーン: (5, 5)（タイル座標）
  - 右端の特定タイル（TILE_WARP）に触れると cave_1 へ遷移
  - cave_1 からの帰還スポーン: (30, 16)（右端付近）

cave_1（洞窟）
  - サイズ: 20×20タイル（320×320ピクセル相当）
  - field_1 からの入場スポーン: (1, 10)（左端付近）
  - 左端の特定タイル（TILE_WARP）に触れると field_1 へ戻る
```

スポーン座標は `.pyxres` マップ制作時に実際のタイル配置に合わせて `params.py` で定義する。

エリア遷移時に自動セーブを実行する。

### エンカウント

草むらタイルに移動するたびに `ENCOUNTER_RATE` で判定。
出現モンスターはエリアごとの出現テーブル（`data/monsters.py` 内に定義）から抽選。

```python
AREA_ENCOUNTER_TABLE = {
    "field_1": [(1, 40), (2, 30), (3, 20), (4, 10)],  # (monster_id, weight)
    "cave_1":  [(5, 35), (6, 35), (7, 20), (8, 10)],
}
```

### カメラ

プレイヤー中心でマップをスクロール。256×256ウィンドウ。
マップ端ではカメラがクランプされる（画面外にマップが出ない）。

### プレイヤー移動

1タイル単位（16px）。歩行2フレームアニメーション。
壁タイル（TILE_BLOCK）には移動不可。

---

## 操作キー定義

| アクション | キー |
|---|---|
| 移動 | 十字キー / WASD |
| 決定・文字送り | Enter / Space |
| メニューを開く | E |
| キャンセル・戻る | Q |

`config/params.py` にリスト形式で定義し、コード内でハードコードしない。

---

## パラメータファイル

```python
# config/params.py
import pyxel

# 画面
SCREEN_WIDTH  = 256
SCREEN_HEIGHT = 256
FPS           = 30
TILE_SIZE     = 16

# パーティ
MAX_PARTY_SIZE = 6

# フィールド
ENCOUNTER_RATE = 0.10   # 草むら1歩ごとの出現確率

# タイル番号
TILE_WALKABLE = list(range(0, 16))
TILE_GRASS    = list(range(16, 20))
TILE_BLOCK    = list(range(32, 64))
TILE_WARP     = list(range(64, 68))

# バトル
CAPTURE_BASE_MULTIPLIER = 1.0
EXP_GAIN_MULTIPLIER     = 1.0
DAMAGE_RANDOM_MIN       = 0.85

# キー
KEY_CONFIRM     = [pyxel.KEY_RETURN, pyxel.KEY_SPACE]
KEY_CANCEL      = [pyxel.KEY_Q]
KEY_MENU        = [pyxel.KEY_E]
KEY_MOVE_UP     = [pyxel.KEY_UP,    pyxel.KEY_W]
KEY_MOVE_DOWN   = [pyxel.KEY_DOWN,  pyxel.KEY_S]
KEY_MOVE_LEFT   = [pyxel.KEY_LEFT,  pyxel.KEY_A]
KEY_MOVE_RIGHT  = [pyxel.KEY_RIGHT, pyxel.KEY_D]
```

---

## UI レイアウト

### バトル画面（256×256px）

```
y=0
┌─────────────────────────────┐
│  [敵スプライト 64x64]         │  y=0〜79   (高さ80px)
│  敵名        HP:██████░░░   │
├─────────────────────────────┤
│  [自スプライト 64x64]         │  y=80〜159 (高さ80px)
│  自名  Lv.15  HP:████████   │
├─────────────────────────────┤  y=160
│  ▶ たたかう    つかまえる     │  y=160〜207 コマンドメニュー
│    にげる      アイテム       │
├─────────────────────────────┤  y=208
│  メッセージ行1                │  y=208〜255 メッセージウィンドウ
│  メッセージ行2                │  (2行、文字送りあり)
└─────────────────────────────┘  y=256
```

### メニュー画面

Eキーで開くメニューの項目:
1. **てもち** — 手持ちモンスター一覧（HP表示）
2. **ずかん** — 捕まえたモンスター一覧（caught_ids ベース）
3. **バッグ** — 所持アイテム（Phase A: モンスターボールのみ）
4. **セーブ** — ゲームを保存
5. **もどる** — メニューを閉じる

### フィールド画面

- 画面右上に現在地名を表示（小フォント）
- Eキーでメニューを開く

---

## タイトル画面・新規ゲーム

1. タイトル画面: ゲーム名 + 「Press Enter」表示
2. Enterで開始 → `save.json` が存在すれば「つづきから / はじめから」を選択
3. 「はじめから」選択時: プレイヤー名入力（文字選択UI、最大8文字）
4. 最初のモンスター1匹を選ぶ（3匹から選択）
5. `field_1` のスタート地点でフィールド開始

---

## セーブデータ

**ファイルパス:** `main.py` と同じディレクトリに `save.json` を保存。

**エラーハンドリング:** `save.json` が存在しない or 壊れている場合はサイレントに無視し、新規ゲーム扱いとする（クラッシュしない）。

```json
{
  "player": {
    "name": "レッド",
    "pos": [10, 15],
    "area": "field_1"
  },
  "party": [
    {
      "spec_id": 3,
      "level": 12,
      "current_hp": 45,
      "max_hp": 58,
      "exp": 240,
      "move_ids": [1, 5, 12, -1]
    }
  ],
  "caught_ids": [1, 3, 7],
  "items": {"pokeball": 5}
}
```

**move_ids:** 技IDの配列（最大4要素）。`-1` は空きスロット。
ロード時は `moves.py` の辞書（`{id: Move}`）を参照して `Move` オブジェクトに変換する。

**area:** エリアID文字列。有効値: `"field_1"`, `"cave_1"`。

セーブタイミング: メニューから手動セーブ + エリア遷移時の自動セーブ。

---

## モンスターデータ

- Phase A: 15〜25匹
- タイプは最大2種
- エリアごとに出現テーブルを分ける（上記 `AREA_ENCOUNTER_TABLE` 参照）
- **スターター:** ID 1, 2, 3 をスターターとして予約（炎・水・草タイプを1体ずつ）。フィールドでは出現しない
- 野生モンスター: ID 4 以降

---

## 開発環境

- Python 3.12+
- uv（パッケージ管理）
- Pyxel（最新版）
- 解像度: 256×256
