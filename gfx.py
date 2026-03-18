# gfx.py
"""Shared drawing helpers — Japanese bitmap font rendering."""
from __future__ import annotations
import pyxel

# umplus: ドット絵向けビットマップフォント（pyxel copy_examples で取得）
_FONT_PATH = "assets/umplus_j10r.bdf"
_font: "pyxel.Font | None" = None


def _get_font() -> "pyxel.Font":
    global _font
    if _font is None:
        _font = pyxel.Font(_FONT_PATH)
    return _font


def jtext(x: int, y: int, s: str, col: int) -> None:
    """日本語対応テキスト描画。"""
    pyxel.text(x, y, s, col, _get_font())


def text_width(s: str) -> int:
    """文字列の描画幅を返す。"""
    return _get_font().text_width(s)
