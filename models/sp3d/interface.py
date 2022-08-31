from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

Back: TypeAlias = float
Left: TypeAlias = float
Bottom: TypeAlias = float
Corner: TypeAlias = tuple[Back, Left, Bottom]

Depth: TypeAlias = float
Width: TypeAlias = float
Height: TypeAlias = float
Shape: TypeAlias = tuple[Depth, Width, Height]

Image: TypeAlias = npt.NDArray[np.uint8]


@dataclass
class Block:
    name: str
    shape: Shape
    rotatable_axes: tuple[int] = (0, 1, 2)

    def copy(self) -> Block:
        return Block(**asdict(self))

    def choice_rotate_axis(self, rng: random.Random) -> int:
        return rng.choice(self.rotatable_axes)

    def rotate(self, axis: int) -> None:
        assert axis in self.rotatable_axes and isinstance(axis, int)
        i = (axis + 1) % 3
        j = (axis + 2) % 3
        self.shape[i], self.shape[j] = self.shape[j], self.shape[i]
        rotatable_axes = (axis,)
        if i in self.rotatable_axes:
            rotatable_axes += (j,)
        if j in self.rotatable_axes:
            rotatable_axes += (i,)
        self.rotatable_axes = rotatable_axes


@dataclass
class Request:
    container_shape: Shape
    blocks: list[Block]

    @property
    def n_blocks(self) -> int:
        return len(self.blocks)


@dataclass
class Response:
    blocks: list[Block]
    corners: list[Corner]
