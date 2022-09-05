import math
import random
import sys
import time
from typing import Iterator

import cv2

from models.sp3d.interface import INF, Block, Corner, Image, Request, Response
from models.sp3d.logger import get_logger
from models.sp3d.utils import calc_score_and_corner
from models.sp3d.visualizer import Visulalizer


class Solver:
    def __init__(
        self,
        request: Request,
        rng: random.Random = random.Random(),
    ) -> None:
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = self.__initialized_order()

        score, corners = self.__calc_depth_and_corners()
        self.score: float = score
        self.corners: list[Corner] = corners

        self.opt_score: float = score
        self.opt_blocks: list[Block] = [block.copy() for block in self.blocks]
        self.opt_corners: list[Corner] = corners

        self.visualizer = Visulalizer(self.request.container_shape)

    def __initialized_order(self) -> list[int]:
        return [
            idx
            for idx, _ in sorted(
                enumerate(self.blocks), key=lambda t: t[1].volume, reverse=True
            )
        ]

    def __calc_depth_and_corners(self) -> tuple[float, list[Corner]]:
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
        corners: list[Corner] = [(0.0, 0.0, 0.0)] * len(self.blocks)
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            (container_depth, -INF, -INF),
            (-INF, container_width, -INF),
            # (-INF, -INF, container_height),
        ]
        max_score = 0.0
        for order in self.packing_order:
            block = self.blocks[order]
            score, corner = calc_score_and_corner(block, blocks, _corners)
            max_score = max(max_score, score)
            blocks.append(block)
            _corners.append(corner)
        for idx, order in enumerate(self.packing_order):
            corners[order] = _corners[idx + 5]
        return max_score, corners

    def __swap(self, temparature: float) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2],
            self.packing_order[idx1],
        )
        score, corners = self.__calc_depth_and_corners()
        diff = score - self.score
        transit = math.log(self.rng.random()) * temparature <= -diff
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
        score, corners = self.__calc_depth_and_corners()
        diff = score - self.score
        transit = math.log(self.rng.random()) * temparature <= -diff
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

    def loop(
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
    ) -> Response:
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
        response = Response(self.blocks, self.opt_corners)
        return response
