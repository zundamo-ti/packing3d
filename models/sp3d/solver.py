import math
import random
import sys
import time
from typing import Iterator

import cv2

from models.sp3d.interface import (
    INF,
    Block,
    Corner,
    Image,
    Request,
    Response,
    Shape,
)
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
        self.packing_order = list(range(self.request.n_blocks))
        self.temparature: float = 0.0

        depth, corners = self.__calc_depth_and_corners()
        self.depth: float = depth
        self.corners: list[Corner] = corners

        self.opt_depth: float = depth
        self.opt_corners: list[Corner] = corners

        self.visualizer = Visulalizer(self.request.container_shape)

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
            (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
            (3 * INF, 3 * INF, 3 * INF),
        ]
        corners: list[Corner] = [(0.0, 0.0, 0.0)] * len(self.blocks)
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            (container_depth, -INF, -INF),
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
            corners[order] = _corners[idx + 6]
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
        if transit:
            self.opt_depth = self.depth
            self.opt_corners = self.corners.copy()
        return transit

    def loop(self, max_iter: int) -> Iterator[Image]:
        for n_iter in range(1, max_iter + 1):
            self.transit()
            if n_iter % 100 == 0:
                yield self.render()

    def render(self, size: int = 500, padding: int = 20) -> Image:
        return self.visualizer.render(self.blocks, self.corners, size, padding)

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

    def random_shape(rng: random.Random) -> Shape:
        return (rng.random() * 50, rng.random() * 50, rng.random() * 50)

    rng = random.Random()

    blocks = [
        Block("block1", random_shape(rng), (0, 0, 255)),
        Block("block2", random_shape(rng), (0, 255, 0)),
        Block("block3", random_shape(rng), (255, 0, 0)),
        Block("block4", random_shape(rng), (0, 255, 255)),
        Block("block5", random_shape(rng), (255, 255, 0)),
        Block("block6", random_shape(rng), (255, 0, 255)),
    ]
    request = Request((100.0, 100.0, 100.0), blocks)
    solver = Solver(request)
    print(f"{solver.corners=}")
    image = solver.render()
    try:
        cv2.imshow("", image)
        while True:
            if cv2.waitKey(1) & 0xFF == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
