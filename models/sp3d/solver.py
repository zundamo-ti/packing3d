import math
import random
import sys
import time
from typing import Iterator

import cv2

from models.sp3d.interface import INF, Block, Color, Corner, Image, Request, Response, Shape
from models.sp3d.logger import get_logger
from models.sp3d.utils import calc_front_and_corner
from models.sp3d.visualizer import Visulalizer


class Solver:
    def __init__(
        self, request: Request, rng: random.Random = random.Random()
    ) -> None:
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = self.__initialized_order()
        self.temparature: float = 0.0

        depth, corners = self.__calc_depth_and_corners()
        self.depth: float = depth
        self.corners: list[Corner] = corners

        self.opt_depth: float = depth
        self.opt_corners: list[Corner] = corners

        self.visualizer = Visulalizer(self.request.container_shape)

    def __initialized_order(self) -> list[int]:
        return [
            idx for idx, _ in sorted(
                enumerate(self.blocks), key=lambda t: t[1].volume, reverse=True
            )
        ]

    def __calc_depth_and_corners(self) -> tuple[float, list[Corner]]:
        (
            container_depth,
            container_width,
            container_height,
        ) = self.request.container_shape
        shapes: list[Shape] = [
            (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
            # (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
        ]
        corners: list[Corner] = [(0.0, 0.0, 0.0)] * len(self.blocks)
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            # (container_depth, -INF, -INF),
            (-INF, container_width, -INF),
            (-INF, -INF, container_height),
        ]
        max_depth = 0.0
        for order in self.packing_order:
            new_shape = self.blocks[order].shape
            depth, corner = calc_front_and_corner(new_shape, shapes, _corners)
            max_depth = max(max_depth, depth)
            shapes.append(new_shape)
            _corners.append(corner)
        for idx, order in enumerate(self.packing_order):
            corners[order] = _corners[idx + 5]
        return max_depth, corners

    def __swap(self) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2],
            self.packing_order[idx1],
        )
        depth, corners = self.__calc_depth_and_corners()
        diff = depth - self.depth
        transit = math.log(self.rng.random()) * self.temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.depth = depth
        else:
            # rollback
            self.packing_order[idx1], self.packing_order[idx2] = (
                self.packing_order[idx2],
                self.packing_order[idx1],
            )
        return transit

    def __rotate(self) -> bool:
        idx = self.rng.choice(range(self.request.n_blocks))
        axis = self.blocks[idx].choice_rotate_axis(self.rng)
        # rotate
        self.blocks[idx].rotate(axis)
        depth, corners = self.__calc_depth_and_corners()
        diff = depth - self.depth
        transit = math.log(self.rng.random()) * self.temparature <= -diff
        if transit:
            # update
            self.corners = corners
            self.depth = depth
        else:
            # rollback
            self.blocks[idx].rotate(axis)
        return transit

    def transit(self) -> bool:
        if self.rng.random() < 0.5:
            transit = self.__swap()
        else:
            transit = self.__rotate()
        if transit and self.depth <= self.opt_depth:
            self.opt_depth = self.depth
            self.opt_corners = self.corners.copy()
        return transit

    def loop(self, max_iter: int, size: int, padding: int) -> Iterator[tuple[float, Image]]:
        for n_iter in range(1, max_iter + 1):
            if n_iter % 1 == 0:                
                yield self.opt_depth, self.render(size, padding)
            self.transit()

    def render(self, size: int, padding: int) -> Image:
        return self.visualizer.render(self.blocks, self.opt_corners, size, padding)

    def solve(self, max_iter: int) -> Response:
        try:
            self.logger.info("start solving ...")
            start = time.time()
            for n_iter in range(max_iter):
                self.transit()
                if n_iter % 100 == 0:
                    t = time.time() - start
                    self.logger.info(
                        f"optimal depth: {self.opt_depth}"
                        f"in {int(t * 100) / 100} seconds."
                    )
            self.logger.info("finish solving !")
        except KeyboardInterrupt:
            self.logger.info("keyboard interrupted")
        response = Response(self.blocks, self.opt_corners)
        return response


if __name__ == "__main__":
    import os
    def random_shape(block_size: int, rng: random.Random) -> Shape:
        min_size = block_size // 10
        max_size = 3 * block_size // 10
        return (
            5 * rng.randint(min_size, max_size),
            5 * rng.randint(min_size, max_size),
            5 * rng.randint(min_size, max_size),
        )

    def random_color(rng: random.Random) -> Color:
        return (
            rng.randint(0, 255),
            rng.randint(0, 255),
            rng.randint(0, 255),
        )

    rng = random.Random()
    block_size = 40
    n_blocks = 12
    container_shape = (150, 100, 100)
    max_iter = 100
    size = 500
    padding = 20
    blocks = [
        Block(f"block{i}", random_shape(block_size, rng), random_color(rng))
        for i in range(n_blocks)
    ]
    request = Request(container_shape, blocks)
    solver = Solver(request)
    image = solver.render(size, padding)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter("./movie.mp4", fourcc, 20.0, image.shape[:2][::-1])
    try:
        for image in solver.loop(max_iter, size, padding):
            cv2.imshow("", image)
            cv2.waitKey(1)
            writer.write(image)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
