import copy
import math
import random
import sys
import time
from typing import Iterator, TextIO

import numpy as np

from src.interface import INF, Block, Corner, Image, Request, StripPackingResponse
from src.logger import get_logger
from src.utils import calc_top_height_and_corner
from src.visualizer import Visulalizer


class StripPackingSolver:
    def __init__(
        self,
        request: Request,
        rng: random.Random = random.Random(),
    ) -> None:
        start = time.time()
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = self.__initialized_order()

        score, corners = self.__calc_score_and_corners()
        self.score: float = score
        self.corners: list[Corner] = corners

        self.opt_score: float = score
        self.opt_blocks: list[Block] = [block.copy() for block in self.blocks]
        self.opt_corners: list[Corner] = corners

        self.visualizer = Visulalizer(self.request.container_shape)
        self.logger.info(f"Initialized in {int(100 * (time.time() - start)) / 100} seconds")

    def __initialized_order(self) -> list[int]:
        return [
            idx
            for idx, _ in sorted(
                enumerate(self.blocks), key=lambda t: (t[1].stackable, t[1].volume), reverse=True
            )
        ]

    def __calc_score_and_corners(self) -> tuple[float, list[Corner]]:
        (
            container_depth,
            container_width,
            container_height,
        ) = self.request.container_shape
        blocks = [
            Block(
                "wall1", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall2", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall3", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall4", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall5", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            # Block(f"wall6", (3 * INF, 3 * INF, 3 * INF),
            # (0, 0, 0), stackable=True),
        ]
        n_walls = len(blocks)
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            (container_depth, -INF, -INF),
            (-INF, container_width, -INF),
            (-INF, -INF, container_height),
        ][:n_walls]
        max_height = 0.0
        n_unstacked = 0
        for order in self.packing_order:
            block = self.blocks[order]
            top_height, corner = calc_top_height_and_corner(block, blocks, _corners)
            if top_height >= INF:
                n_unstacked += 1
            else:
                max_height = max(max_height, top_height)
            blocks.append(block)
            _corners.append(corner)
        corners: list[Corner] = [(0.0, 0.0, 0.0)] * len(self.blocks)
        for idx, order in enumerate(self.packing_order):
            corners[order] = _corners[idx + n_walls]
        score = max_height + n_unstacked * INF
        return score, corners

    def __swap(self, temparature: float) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2],
            self.packing_order[idx1],
        )
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.packing_order[idx1], self.packing_order[idx2] = (
                self.packing_order[idx2],
                self.packing_order[idx1],
            )
        return transit

    def __rotate(self, temparature: float) -> bool:
        idx = self.rng.choice(range(self.request.n_blocks))
        axis = self.blocks[idx].choice_rotate_axis(self.rng)
        # rotate
        self.blocks[idx].rotate(axis)
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.blocks[idx].rotate(axis)
        return transit

    def transit(self, allow_rotate: bool, temparature: float) -> bool:
        if self.rng.random() < 0.5 or not allow_rotate:
            transit = self.__swap(temparature)
        else:
            transit = self.__rotate(temparature)
        if transit and self.score <= self.opt_score:
            self.opt_score = self.score
            self.opt_blocks = [block.copy() for block in self.blocks]
            self.opt_corners = self.corners.copy()
        return transit

    def loop_render(
        self,
        max_iter: int,
        allow_rotate: bool,
        temparature: float,
        size: int,
        padding: int,
    ) -> Iterator[tuple[float, Image]]:
        for n_iter in range(1, max_iter + 1):
            if n_iter % 10 == 0:
                yield self.opt_score, self.render(size, padding)
            self.transit(allow_rotate, temparature)

    def render(self, size: int, padding: int) -> Image:
        return self.visualizer.render(
            self.opt_blocks, self.opt_corners, size, padding
        )

    def solve(
        self,
        max_iter: int,
        allow_rotate: bool,
        temparature: float,
    ) -> StripPackingResponse:
        try:
            self.logger.info("start solving ...")
            start = time.time()
            for n_iter in range(max_iter):
                if self.opt_score <= self.request.container_shape[2]:
                    break
                self.transit(allow_rotate, temparature)
                if n_iter % 100 == 0:
                    t = time.time() - start
                    self.logger.info(
                        f"optimal score: {self.opt_score}"
                        f"in {int(t * 100) / 100} seconds."
                    )
            self.logger.info("finish solving !")
        except KeyboardInterrupt:
            self.logger.info("keyboard interrupted")
        response = StripPackingResponse(self.blocks, self.opt_corners)
        return response

StartAndEndIndex = tuple[int, int]


class BinPackingSolver:
    def __init__(
        self,
        request: Request,
        rng: random.Random = random.Random()
    ) -> None:
        start = time.time()
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = self.__initialized_order()

        score, corners = self.__calc_score_and_corners()
        self.score: float = score
        self.corners: list[tuple[int, list[Corner]]] = corners

        self.opt_score: float = score
        self.opt_blocks: list[Block] = [block.copy() for block in self.blocks]
        self.opt_corners: list[tuple[int, list[Corner]]] = corners
        self.opt_packing_order = self.packing_order.copy()

        self.visualizer = Visulalizer(self.request.container_shape)
        self.logger.info(f"Initialized in {(time.time() - start):.2f} seconds")

    def __initialized_order(self) -> list[int]:
        packing_order = list(range(self.request.n_blocks))
        self.rng.shuffle(packing_order)
        return packing_order

    def __calc_top_height_and_corners_and_last_idx(self, start_idx: int) -> tuple[float, list[Corner], int]:
        (
            container_depth,
            container_width,
            container_height,
        ) = self.request.container_shape
        blocks = [
            Block(
                "wall1", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall2", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall3", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall4", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall5", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
            Block(
                "wall6", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
            ),
        ]
        n_walls = len(blocks)
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            (container_depth, -INF, -INF),
            (-INF, container_width, -INF),
            (-INF, -INF, container_height),
        ][:n_walls]
        max_height = 0.0
        for idx in range(start_idx, self.request.n_blocks):
            end_idx = idx
            order = self.packing_order[idx]
            block = self.blocks[order]
            top_height, corner = calc_top_height_and_corner(block, blocks, _corners, n_walls - 1)
            if top_height >= INF:
                end_idx -= 1
                break
            else:
                max_height = max(max_height, top_height)
            blocks.append(block)
            _corners.append(corner)
        corners: list[Corner] = [(0.0, 0.0, 0.0)] * (end_idx - start_idx + 1)
        for idx in range(end_idx - start_idx + 1):
            corners[idx] = _corners[idx + n_walls]
        return max_height, corners, end_idx

    def __calc_score_and_corners(self) -> tuple[float, list[tuple[StartAndEndIndex, list[Corner]]]]:
        start_idx = 0
        n_containers = 0
        n_blocks_in_last_container = 0
        packing_factor_in_last_container = 0.0
        all_corners: list[tuple[int, list[Corner]]] = []
        for container_idx in range(self.request.n_blocks):
            if start_idx == self.request.n_blocks:
                break
            (
                top_height, corners, end_idx
            ) = self.__calc_top_height_and_corners_and_last_idx(start_idx)
            n_blocks_in_last_container = len(corners)
            packing_factor_in_last_container = sum(
                self.blocks[self.packing_order[idx]].volume for idx in range(start_idx, end_idx + 1)
            ) / self.request.container_volume
            n_containers += 1
            all_corners.append(((start_idx, end_idx), corners))
            if start_idx == end_idx:
                break
            start_idx = end_idx + 1
        score = packing_factor_in_last_container + n_containers * INF
        return score, all_corners

    def __swap(self, temparature: float) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2],
            self.packing_order[idx1],
        )
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.packing_order[idx1], self.packing_order[idx2] = (
                self.packing_order[idx2],
                self.packing_order[idx1],
            )
        return transit

    def __rotate(self, temparature: float) -> bool:
        idx = self.rng.choice(range(self.request.n_blocks))
        axis = self.blocks[idx].choice_rotate_axis(self.rng)
        # rotate
        self.blocks[idx].rotate(axis)
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.blocks[idx].rotate(axis)
        return transit

    def transit(self, allow_rotate: bool, temparature: float) -> bool:
        if self.rng.random() < 0.5 or not allow_rotate:
            transit = self.__swap(temparature)
        else:
            transit = self.__rotate(temparature)
        if transit and self.score <= self.opt_score:
            self.opt_score = self.score
            self.opt_blocks = [block.copy() for block in self.blocks]
            self.opt_packing_order = self.packing_order.copy()
            self.opt_corners = copy.deepcopy(self.corners)
        return transit

    def loop_render(
        self,
        max_iter: int,
        allow_rotate: bool,
        temparature: float,
        size: int,
        padding: int,
    ) -> Iterator[tuple[float, Image]]:
        for n_iter in range(1, max_iter + 1):
            if n_iter % 10 == 0:
                yield self.opt_score, self.render(size, padding)
            self.transit(allow_rotate, temparature)

    def render(self, size: int, padding: int) -> Image:
        images: list[Image] = []
        for (start_idx, end_idx), corners in self.opt_corners:
            blocks = [
                self.opt_blocks[self.opt_packing_order[idx]] for idx in range(start_idx, end_idx + 1)
            ]
            images.append(self.visualizer.render(blocks, corners, size, padding))
        if len(images) == 0:
            raise
        elif len(images) == 1:
            image = images[0]
        else:
            image = np.concatenate(images, axis=0)
        return image


class BinPackingSolver2:
    def __init__(
        self,
        request: Request,
        rng: random.Random = random.Random()
    ) -> None:
        start = time.time()
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = self.__initialized_order()

        score, corners = self.__calc_score_and_corners()
        self.score: float = score
        self.corners: list[tuple[int, list[Corner]]] = corners

        self.opt_score: float = score
        self.opt_blocks: list[Block] = [block.copy() for block in self.blocks]
        self.opt_corners: list[tuple[int, list[Corner]]] = corners
        self.opt_packing_order = self.packing_order.copy()

        self.visualizer = Visulalizer(self.request.container_shape)
        self.logger.info(f"Initialized in {(time.time() - start):.2f} seconds")

    def __initialized_order(self) -> list[int]:
        return [
            idx
            for idx, _ in sorted(
                enumerate(self.blocks), key=lambda t: (t[1].stackable, t[1].volume), reverse=True
            )
        ]

    def __calc_score_and_corners(self) -> tuple[float, list[tuple[int, Corner]]]:
        (
            container_depth,
            container_width,
            container_height,
        ) = self.request.container_shape
        _blocks_by_container: list[list[Block]] = []
        NUM_WALLS = 6
        CEIL_INDEX = 5
        corners: list[tuple[int, Corner]] = []
        _corners_by_container: list[list[Corner]] = []
        for block_idx in range(self.request.n_blocks):
            order = self.packing_order[block_idx]
            block = self.blocks[order]
            top_height = INF
            for container_idx, (_blocks, _corners) in enumerate(zip(_blocks_by_container, _corners_by_container)):
                top_height, corner = calc_top_height_and_corner(block, _blocks, _corners, CEIL_INDEX)
                if top_height >= INF:
                    continue
                _blocks.append(block)
                _corners.append(corner)
                idx = container_idx
                corners.append((idx, corner))
                break
            if top_height >= INF:
                _blocks = [
                    Block(
                        "wall1", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                    Block(
                        "wall2", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                    Block(
                        "wall3", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                    Block(
                        "wall4", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                    Block(
                        "wall5", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                    Block(
                        "wall6", (3 * INF, 3 * INF, 3 * INF), (0, 0, 0), stackable=True
                    ),
                ]
                _blocks_by_container.append(_blocks)
                _corners: list[Corner] = [
                    (-3 * INF, -INF, -INF),
                    (-INF, -3 * INF, -INF),
                    (-INF, -INF, -3 * INF),
                    (container_depth, -INF, -INF),
                    (-INF, container_width, -INF),
                    (-INF, -INF, container_height),
                ]
                _corners_by_container.append(_corners)
                top_height, corner = calc_top_height_and_corner(block, _blocks, _corners, CEIL_INDEX)
                if top_height >= INF:
                    raise ValueError(f"too large block: {block.shape=}")
                _blocks.append(block)
                _corners.append(corner)
                idx = len(_blocks_by_container) - 1
                corners.append((idx, corner))
        n_containers = len(_blocks_by_container)
        n_blocks_in_last_container = len(_blocks_by_container[-1]) - NUM_WALLS
        score = n_blocks_in_last_container + n_containers * INF
        return score, corners

    def __swap(self, temparature: float) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2],
            self.packing_order[idx1],
        )
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.packing_order[idx1], self.packing_order[idx2] = (
                self.packing_order[idx2],
                self.packing_order[idx1],
            )
        return transit

    def __rotate(self, temparature: float) -> bool:
        idx = self.rng.choice(range(self.request.n_blocks))
        axis = self.blocks[idx].choice_rotate_axis(self.rng)
        # rotate
        self.blocks[idx].rotate(axis)
        score, corners = self.__calc_score_and_corners()
        diff = score - self.score
        rnd = 1e-9 + self.rng.random() * (1 - 1e-9)
        transit = math.log(rnd) * temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.score = score
        else:
            # rollback
            self.blocks[idx].rotate(axis)
        return transit

    def transit(self, allow_rotate: bool, temparature: float) -> bool:
        if self.rng.random() < 0.5 or not allow_rotate:
            transit = self.__swap(temparature)
        else:
            transit = self.__rotate(temparature)
        if transit and self.score <= self.opt_score:
            self.opt_score = self.score
            self.opt_blocks = [block.copy() for block in self.blocks]
            self.opt_packing_order = self.packing_order.copy()
            self.opt_corners = copy.deepcopy(self.corners)
        return transit

    def loop_render(
        self,
        max_iter: int,
        allow_rotate: bool,
        temparature: float,
        size: int,
        padding: int,
    ) -> Iterator[tuple[float, Image]]:
        for n_iter in range(1, max_iter + 1):
            if n_iter % 10 == 0:
                yield self.opt_score, self.render(size, padding)
            self.transit(allow_rotate, temparature)

    def render(self, size: int, padding: int) -> Image:
        n_containers = max(map(lambda t: t[0], self.opt_corners)) + 1
        blocks_by_container: list[list[Block]] = [[] for _ in range(n_containers)]
        corners_by_container: list[list[Corner]] = [[] for _ in range(n_containers)]
        for idx in range(self.request.n_blocks):
            order = self.packing_order[idx]
            container_idx, corner = self.opt_corners[idx]
            block = self.opt_blocks[order]
            blocks_by_container[container_idx].append(block)
            corners_by_container[container_idx].append(corner)
        images = [
            self.visualizer.render(block, corner, size, padding)
            for block, corner in zip(blocks_by_container, corners_by_container)
        ]
        if len(images) == 1:
            return images[0]
        else:
            return np.concatenate(images, axis=0)
