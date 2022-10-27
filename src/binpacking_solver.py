import itertools
import math
import random
import sys
import time
from typing import Iterator

import numpy as np
from pulp import (
    PULP_CBC_CMD,
    LpBinary,
    LpMinimize,
    LpProblem,
    LpStatusOptimal,
    LpVariable,
    lpSum,
)

from src.interface import (
    INF,
    BinPackingRequest,
    BinPackingResponse,
    Block,
    Container,
    Corner,
    Image,
)
from src.logger import get_logger
from src.utils import calc_top_height_and_corner
from src.visualizer import Visulalizer

VOLUME_CAPACITY_RATIO = 0.7
AREA_CAPACITY_RATIO = 1.0
WEIGHT_CAPACITY_RATIO = 1.0
BIG_NUMBER = 1e9
WALLS = [
    Block(
        "wall1", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
    Block(
        "wall2", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
    Block(
        "wall3", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
    Block(
        "wall4", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
    Block(
        "wall5", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
    Block(
        "wall6", (3 * INF, 3 * INF, 3 * INF), 0.0, (0, 0, 0), stackable=True
    ),
]
N_WALLS = len(WALLS)
CONTAINER_USED_PENALTY = 1e5
BLOCK_UNSTACKED_PENALTY = 1e10


class BinPackingSolver:
    def __init__(
        self,
        request: BinPackingRequest,
        rng: random.Random = random.Random(),
    ) -> None:
        self.request = request
        self.rng = rng
        self.logger = get_logger(self.__class__.__name__, sys.stdout)
        self.initialize()
        self.visualizers = [
            Visulalizer(container.shape)
            for container in self.request.containers
        ]
        self.temparature = 0.0

    def response(self) -> BinPackingResponse:
        container_indexes: list[int] = [-1] * self.request.n_blocks
        corners: list[Corner] = [(INF, INF, INF)] * self.request.n_blocks
        for container_idx, block_idxs, _corners in zip(
            range(self.request.n_containers),
            self.assigned_block_idxs,
            self.assigned_corners,
        ):
            for block_idx, corner in zip(block_idxs, _corners):
                container_indexes[block_idx] = container_idx
                corners[block_idx] = corner
        return BinPackingResponse(container_indexes, corners)

    def initialize(self) -> None:
        self.blocks = [block.copy() for block in self.request.blocks]
        self.assigned_block_idxs = self.initial_assignment()
        self.assigned_corners: list[list[Corner]] = []
        self.assigned_scores: list[float] = []
        self.total_score = 0.0
        n_containers = 0
        for container, block_idxs in zip(
            self.request.containers, self.assigned_block_idxs
        ):
            if len(block_idxs) > 0:
                n_containers += 1
            score, corners = self.__calc_score_and_corners(
                container, block_idxs
            )
            self.total_score += score
            self.assigned_corners.append(corners)
            self.assigned_scores.append(score)
        self.total_score += CONTAINER_USED_PENALTY * n_containers

    def render(self, size: int, padding: int) -> Image:
        images: list[Image] = []
        for visualizer, block_idxs, corners in zip(
            self.visualizers, self.assigned_block_idxs, self.assigned_corners
        ):
            blocks = [self.blocks[idx] for idx in block_idxs]
            image = visualizer.render(blocks, corners, size, padding)
            images.append(image)
        return np.concatenate(images)

    def __calc_score_and_corners(
        self, container: Container, block_idxs: list[int]
    ) -> tuple[float, list[Corner]]:
        wall_and_blocks = WALLS.copy()
        container_depth, container_width, container_height = container.shape
        _corners: list[Corner] = [
            (-3 * INF, -INF, -INF),
            (-INF, -3 * INF, -INF),
            (-INF, -INF, -3 * INF),
            (container_depth, -INF, -INF),
            (-INF, container_width, -INF),
            (-INF, -INF, container_height),
        ]
        max_height = 0.0
        n_unstacked = 0
        for idx in block_idxs:
            block = self.blocks[idx]
            top_height, corner = calc_top_height_and_corner(
                block, wall_and_blocks, _corners, N_WALLS - 1
            )
            if top_height >= INF:
                n_unstacked += 1
            else:
                max_height = max(max_height, top_height)
            wall_and_blocks.append(block)
            _corners.append(corner)
        score = max_height + BLOCK_UNSTACKED_PENALTY * n_unstacked
        corners = _corners[N_WALLS:]
        return score, corners

    def initial_assignment(self) -> list[list[int]]:
        problem = LpProblem("Initialize", LpMinimize)
        assignment = {
            (i, j): LpVariable(
                f"assign_block{i}_to_container{j}", cat=LpBinary
            )
            for i, j in itertools.product(
                range(self.request.n_blocks), range(self.request.n_containers)
            )
        }
        use = [
            LpVariable(f"use_container{i}", cat=LpBinary)
            for i in range(self.request.n_containers)
        ]
        problem.setObjective(lpSum(use))
        for j in range(self.request.n_containers):
            problem.addConstraint(
                lpSum(
                    assignment[i, j] * self.request.blocks[i].volume
                    for i in range(self.request.n_blocks)
                )
                <= use[j]
                * self.request.containers[j].volume
                * VOLUME_CAPACITY_RATIO
            )
            problem.addConstraint(
                lpSum(
                    assignment[i, j] * self.request.blocks[i].weight
                    for i in range(self.request.n_blocks)
                )
                <= use[j]
                * self.request.containers[j].weight_capacity
                * WEIGHT_CAPACITY_RATIO
            )
            problem.addConstraint(
                lpSum(
                    assignment[i, j] * self.request.blocks[i].base_area
                    for i in range(self.request.n_blocks)
                    if not self.request.blocks[i].stackable
                )
                <= use[j]
                * self.request.containers[j].base_area
                * AREA_CAPACITY_RATIO
            )
        for i in range(self.request.n_blocks):
            problem.addConstraint(
                lpSum(
                    assignment[i, j] for j in range(self.request.n_containers)
                )
                == 1
            )
        solver = PULP_CBC_CMD(timeLimit=30, gapRel=0.01)
        status = problem.solve(solver)
        if status != LpStatusOptimal:
            raise NotImplementedError
        assigned_blocks = [
            sorted(
                [
                    i
                    for i in range(self.request.n_blocks)
                    if assignment[i, j].varValue == 1
                ],
                key=lambda i: self.request.blocks[i].volume
                + BIG_NUMBER * (not self.request.blocks[i].stackable),
            )
            for j in range(self.request.n_containers)
        ]
        return assigned_blocks

    def __rotate(self, temparature: float) -> bool:
        container_idx = self.rng.choice(
            [
                idx
                for idx in range(self.request.n_containers)
                if len(self.assigned_block_idxs[idx]) > 0
            ]
        )
        container = self.request.containers[container_idx]
        block_idxs = self.assigned_block_idxs[container_idx]
        block_idx = self.rng.choice(block_idxs)
        axis = self.blocks[block_idx].choice_rotate_axis(self.rng)
        self.blocks[block_idx].rotate(axis)
        score, corners = self.__calc_score_and_corners(container, block_idxs)
        diff = score - self.assigned_scores[container_idx]
        if math.log(self.rng.random()) * temparature <= -diff:
            self.assigned_corners[container_idx] = corners
            self.assigned_scores[container_idx] = score
            self.total_score += diff
            return True
        self.blocks[block_idx].rotate(axis)
        return False

    def __swap(self, temparature: float) -> bool:
        container_idx = self.rng.choice(
            [
                idx
                for idx in range(self.request.n_containers)
                if len(self.assigned_block_idxs[idx]) > 0
            ]
        )
        block_idxs = self.assigned_block_idxs[container_idx]
        idx1, idx2 = self.rng.choices(range(len(block_idxs)), k=2)
        block_idxs[idx1], block_idxs[idx2] = block_idxs[idx2], block_idxs[idx1]
        container = self.request.containers[container_idx]
        score, corners = self.__calc_score_and_corners(container, block_idxs)
        diff = score - self.assigned_scores[container_idx]
        if math.log(self.rng.random()) * temparature <= -diff:
            self.assigned_corners[container_idx] = corners
            self.assigned_scores[container_idx] = score
            self.total_score += diff
            return True
        block_idxs[idx1], block_idxs[idx2] = block_idxs[idx2], block_idxs[idx1]
        return False

    def __shift(self, temparature: float) -> bool:
        container_idx1, container_idx2 = self.rng.choices(
            [
                idx
                for idx in range(self.request.n_containers)
                if len(self.assigned_block_idxs[idx]) > 0
            ],
            k=2,
        )
        container1 = self.request.containers[container_idx1]
        container2 = self.request.containers[container_idx2]
        block_idxs1 = self.assigned_block_idxs[container_idx1]
        block_idxs2 = self.assigned_block_idxs[container_idx2]
        insert_idx1 = self.rng.randint(0, len(block_idxs1) - 1)
        block_idx = block_idxs1[insert_idx1]
        insert_idx2 = self.rng.randint(0, len(block_idxs2))
        block_idxs1.remove(block_idx)
        block_idxs2.insert(insert_idx2, block_idx)
        score1, corners1 = self.__calc_score_and_corners(
            container1, block_idxs1
        )
        score2, corners2 = self.__calc_score_and_corners(
            container2, block_idxs2
        )
        diff = 0.0
        diff += score1 - self.assigned_scores[container_idx1]
        diff += score2 - self.assigned_scores[container_idx2]
        if math.log(self.rng.random()) * temparature <= -diff:
            self.assigned_corners[container_idx1] = corners1
            self.assigned_corners[container_idx2] = corners2
            self.assigned_scores[container_idx1] = score1
            self.assigned_scores[container_idx2] = score2
            self.total_score += diff
            return True
        block_idxs2.remove(block_idx)
        block_idxs1.insert(insert_idx1, block_idx)
        return False

    def transit(self, temparature: float) -> bool:
        rnd = self.rng.random()
        if rnd < 1 / 3:
            return self.__swap(temparature)
        elif rnd < 2 / 3:
            return self.__rotate(temparature)
        else:
            return self.__shift(temparature)

    def loop_render(
        self,
        max_iter: int,
        temparature: float,
        size: int,
        padding: int,
    ) -> Iterator[tuple[float, Image]]:
        for n_iter in range(1, max_iter + 1):
            if n_iter % 10 == 0:
                yield self.total_score, self.render(size, padding)
            self.transit(temparature)
