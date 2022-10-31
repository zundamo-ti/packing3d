from typing import Optional

import numpy as np
import numpy.typing as npt

from src.error import NoStablePointFound, NoStackablePointFound
from src.interface import INF, Block, Box, Corner, Shape

Length = float
Flag = int
Order = int
Event = tuple[Length, Flag, Order]


def __calc_no_fit_poly(
    new_shape: Shape, shapes: list[Shape], corners: list[Corner]
) -> list[Box]:
    nfps: list[Box] = []
    new_depth, new_width, new_height = new_shape
    for shape, corner in zip(shapes, corners):
        depth, width, height = shape
        back, left, bottom = corner
        box_back = back - new_depth
        box_left = left - new_width
        box_height = bottom - new_height
        box_front = back + depth
        box_right = left + width
        box_top = bottom + height
        nfps.append(
            (box_back, box_front, box_left, box_right, box_height, box_top)
        )
    return nfps


def __calc_events(
    nfps: list[Box],
) -> tuple[list[Event], list[Event], list[Event]]:
    xs = sorted(
        [(box[0], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[1], -1, idx) for idx, box in enumerate(nfps)]
    )
    ys = sorted(
        [(box[2], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[3], -1, idx) for idx, box in enumerate(nfps)]
    )
    zs = sorted(
        [(box[4], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[5], -1, idx) for idx, box in enumerate(nfps)]
    )
    return xs, ys, zs


def __calc_stable_index(
    n_boxes: int,
    xs: list[Event],
    ys: list[Event],
    zs: list[Event],
    stackable: list[bool],
    new_block_is_stackable: bool,
    ceil_idx: Optional[int],
) -> tuple[int, ...]:
    x_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(xs)
    }
    y_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(ys)
    }
    z_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(zs)
    }
    size = 2 * n_boxes
    overlaps = np.zeros((size, size, size), np.int32)
    for idx in range(n_boxes):
        back_order = x_idx_flag_to_order[idx, 1]
        front_order = x_idx_flag_to_order[idx, -1]
        left_order = y_idx_flag_to_order[idx, 1]
        right_order = y_idx_flag_to_order[idx, -1]
        if new_block_is_stackable or idx == ceil_idx:
            bottom_order = z_idx_flag_to_order[idx, 1]
        else:
            bottom_order = 0
        if stackable[idx]:
            top_order = z_idx_flag_to_order[idx, -1]
        else:
            top_order = size - 1

        overlaps[back_order, left_order, bottom_order] += 1
        overlaps[front_order, left_order, bottom_order] -= 1
        overlaps[back_order, right_order, bottom_order] -= 1
        overlaps[back_order, left_order, top_order] -= 1
        overlaps[back_order, right_order, top_order] += 1
        overlaps[front_order, left_order, top_order] += 1
        overlaps[front_order, right_order, bottom_order] += 1
        overlaps[front_order, right_order, top_order] -= 1
    overlaps = np.cumsum(
        np.cumsum(np.cumsum(overlaps, axis=2), axis=1), axis=0
    )
    shifted_back = np.roll(overlaps, shift=1, axis=0)
    shifted_left = np.roll(overlaps, shift=1, axis=1)
    shifted_down = np.roll(overlaps, shift=1, axis=2)
    stable: npt.NDArray[np.int32] = (
        (overlaps == 0)
        & (shifted_back > 0)
        & (shifted_left > 0)
        & (shifted_down > 0)
    )
    stable_indices: list[tuple[int, ...]] = list(zip(*np.where(stable)))
    stable_indices.sort(key=lambda t: (t[0], t[2], t[1]))
    if len(stable_indices) > 0:
        return stable_indices[0]
    else:
        if np.sum(stable) > 0:
            raise NoStackablePointFound
        else:
            raise NoStablePointFound


def calc_container_score_and_corner(
    block: Block,
    blocks: list[Block],
    corners: list[Corner],
    ceil_idx: Optional[int] = None,
) -> tuple[float, Corner]:
    new_shape = block.shape
    shapes = [block.shape for block in blocks]
    nfps = __calc_no_fit_poly(new_shape, shapes, corners)
    n_boxes = len(nfps)
    xs, ys, zs = __calc_events(nfps)
    stackable = [block.stackable for block in blocks]
    try:
        x_idx, y_idx, z_idx = __calc_stable_index(
            n_boxes, xs, ys, zs, stackable, block.stackable, ceil_idx
        )
    except NoStackablePointFound:
        return INF, (INF, INF, INF)
    except NoStablePointFound:
        return INF, (INF, INF, INF)
    x_coord = xs[x_idx][0]
    y_coord = ys[y_idx][0]
    z_coord = zs[z_idx][0]
    front_depth = x_coord + new_shape[0]
    return front_depth, (x_coord, y_coord, z_coord)
