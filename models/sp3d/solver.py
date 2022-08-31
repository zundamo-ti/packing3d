import math
import random
import sys
import time
from typing import Iterator

import cv2
import numpy as np
import numpy.typing as npt

from models.sp3d.interface import Corner, Image, Request, Response, Shape
from models.sp3d.logger import get_logger
from models.sp3d.visualizer import Visulalizer


class Solver:
    def __init__(self, request: Request, rng: random.Random = random.Random()) -> None:
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.blocks = [block.copy() for block in self.request.blocks]
        self.packing_order = list(range(self.request.n_blocks))
        self.temparature: float = 0.0

        depth, corners = self.__calc_depth_and_corners()
        self.depth = depth
        self.corners = corners

        self.opt_depth = depth
        self.opt_corners = corners

        self.visualizer = Visulalizer(self.request.container_shape)

    def __calc_depth_and_corners(self) -> tuple[float, list[Corner]]:
        return 0.0, []

    def __swap(self) -> bool:
        idx1, idx2 = self.rng.choices(range(self.request.n_blocks), k=2)
        # swap
        self.packing_order[idx1], self.packing_order[idx2] = (
            self.packing_order[idx2], self.packing_order[idx1]
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
                self.packing_order[idx2], self.packing_order[idx1]
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
        return self.visualizer.render(size, padding)

    def solve(self, max_iter: int) -> Response:
        try:
            self.logger.info("start solving ...")
            start = time.time()
            for n_iter in range(max_iter):
                self.transit()
                if n_iter % 100 == 0:
                    t = time.time() - start
                    self.logger.info(
                        f"optimal depth: {self.opt_depth} in {int(t * 100) / 100} seconds."
                    )
            self.logger.info("finish solving !")
        except KeyboardInterrupt:
            self.logger.info("keyboard interrupted")
        response = Response(self.blocks, self.opt_corners)
        return response


if __name__ == "__main__":
    request = Request((150.0, 100.0, 100.0), [])
    solver = Solver(request)
    image = solver.render(size=800)
    try:
        cv2.imshow("", image)
        while True:
            if cv2.waitKey(1) & 0xff == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
