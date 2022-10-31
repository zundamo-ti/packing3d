from __future__ import annotations

import random
from dataclasses import dataclass, replace
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

Front: TypeAlias = float
Right: TypeAlias = float
Top: TypeAlias = float
Box: TypeAlias = tuple[Back, Front, Left, Right, Bottom, Top]

Image: TypeAlias = npt.NDArray[np.uint8]
Color: TypeAlias = tuple[int, int, int]

INF = 1e9


def base_area(shape: Shape) -> float:
    depth, width, _ = shape
    return depth * width


def volume(shape: Shape) -> float:
    depth, width, height = shape
    return depth * width * height


@dataclass
class Block:
    name: str
    shape: Shape
    weight: float
    color: Color
    stackable: bool = True
    right_side_up: bool = False

    def __post_init__(self) -> None:
        if self.right_side_up:
            self.rotatable_axes: tuple[int, ...] = (2,)
        else:
            self.rotatable_axes = (0, 1, 2)

    def copy(self) -> Block:
        return replace(self)

    @property
    def volume(self) -> float:
        return volume(self.shape)

    @property
    def base_area(self) -> float:
        return base_area(self.shape)

    def choice_rotate_axis(self, rng: random.Random) -> int:
        return rng.choice(self.rotatable_axes)

    def rotate(self, axis: int) -> None:
        assert axis in self.rotatable_axes and isinstance(axis, int)
        i = (axis + 1) % 3
        j = (axis + 2) % 3
        shape = list(self.shape)
        shape[i], shape[j] = shape[j], shape[i]
        self.shape = tuple(shape)


@dataclass
class Container:
    name: str
    shape: Shape
    weight_capacity: float

    @property
    def volume(self) -> float:
        return volume(self.shape)

    @property
    def base_area(self) -> float:
        return base_area(self.shape)


@dataclass
class Request:
    blocks: list[Block]

    @property
    def n_blocks(self) -> int:
        return len(self.blocks)


@dataclass
class StripPackingRequest(Request):
    container: Container

    @property
    def container_shape(self) -> Shape:
        return self.container.shape

    @property
    def container_volume(self) -> float:
        return volume(self.container.volume)


@dataclass
class BinPackingRequest(Request):
    containers: list[Container]

    @property
    def n_containers(self) -> int:
        return len(self.containers)


@dataclass
class StripPackingResponse:
    blocks: list[Block]
    corners: list[Corner]


@dataclass
class BinPackingResponse:
    blocks: list[Block]
    corners: list[Corner]
    container_indexes: list[int]
