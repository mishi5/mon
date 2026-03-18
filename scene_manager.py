# scene_manager.py
"""Manages scene lifecycle: registration, switching, update/draw dispatch."""
from __future__ import annotations


class Scene:
    """Base class for all scenes."""
    def on_enter(self, **kwargs) -> None: pass
    def on_exit(self) -> None: pass
    def update(self) -> None: pass
    def draw(self) -> None: pass


class SceneManager:
    def __init__(self):
        self.scenes: dict[str, Scene] = {}
        self.current: Scene | None = None

    def register(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def switch(self, name: str, **kwargs) -> None:
        if self.current:
            self.current.on_exit()
        self.current = self.scenes[name]
        self.current.on_enter(**kwargs)

    def update(self) -> None:
        if self.current:
            self.current.update()

    def draw(self) -> None:
        if self.current:
            self.current.draw()
