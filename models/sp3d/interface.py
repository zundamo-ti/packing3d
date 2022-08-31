from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

Back: TypeAlias = float
Left: TypeAlias = float
Bottom: TypeAlias = float
Corner: TypeAlias = tuple[Back, Left, Bottom]

Image: TypeAlias = npt.NDArray[np.uint8]


@dataclass
class Block:
    name: str
    depth: float
    width: float
    height: float

    def copy(self) -> Block:
        return Block(**asdict(self))

    def rotate(self, axis: int) -> None:
        if axis == 0:
            self.width, self.height == self.height, self.width
        elif axis == 1:
            self.depth, self.height = self.height, self.depth
        elif axis == 2:
            self.depth, self.width = self.width, self.depth
        else:
            raise ValueError


@dataclass
class Request:
    blocks: list[Block]

    @property
    def n_blocks(self) -> int:
        return len(self.blocks)


@dataclass
class Response:
    blocks: list[Block]
    corners: list[Corner]
