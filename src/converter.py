import os
import random
from pathlib import Path
from typing import Any

import pandas as pd

from src.interface import (
    Block,
    Container,
    Corner,
    Request,
    Response,
)

# sheet names
CONTAINER_SHEET = "container"
BLOCK_SHEET = "block"
RESPONSE_SHEET = "response"
# column names
BLOCK_NAME = "block_name"
CONTAINER_NAME = "container_name"
DEPTH = "depth"
WIDTH = "width"
HEIGHT = "height"
WEIGHT = "weight"
WEIGHT_CAPACITY = "weight_capacity"
BACK = "back"
LEFT = "left"
BOTTOM = "bottom"
STACKABLE = "stackable"
RIGHT_SIDE_UP = "right_side_up"
# random seed
RNG = random.Random(0)


def blocks_to_df(blocks: list[Block]) -> pd.DataFrame:
    df_blocks_dict: dict[str, list[Any]] = {
        BLOCK_NAME: [],
        DEPTH: [],
        WIDTH: [],
        HEIGHT: [],
        WEIGHT: [],
        STACKABLE: [],
        RIGHT_SIDE_UP: [],
    }
    for block in blocks:
        depth, width, height = block.shape
        df_blocks_dict[BLOCK_NAME].append(block.name)
        df_blocks_dict[DEPTH].append(depth)
        df_blocks_dict[WIDTH].append(width)
        df_blocks_dict[HEIGHT].append(height)
        df_blocks_dict[WEIGHT].append(block.weight)
        df_blocks_dict[STACKABLE].append(block.stackable)
        df_blocks_dict[RIGHT_SIDE_UP].append(block.right_side_up)
    return pd.DataFrame(df_blocks_dict)


def container_to_df(container: Container) -> pd.DataFrame:
    depth, width, height = container.shape
    return pd.DataFrame(
        {
            DEPTH: [depth],
            WIDTH: [width],
            HEIGHT: [height],
            WEIGHT_CAPACITY: [container.weight_capacity],
        }
    )


def containers_to_df(containers: list[Container]) -> pd.DataFrame:
    df_containers_dict: dict[str, list[Any]] = {
        CONTAINER_NAME: [],
        DEPTH: [],
        WIDTH: [],
        HEIGHT: [],
        WEIGHT_CAPACITY: [],
    }
    for container in containers:
        depth, width, height = container.shape
        df_containers_dict[CONTAINER_NAME].append(container.name)
        df_containers_dict[DEPTH].append(depth)
        df_containers_dict[WIDTH].append(width)
        df_containers_dict[HEIGHT].append(height)
        df_containers_dict[WEIGHT_CAPACITY].append(container.weight_capacity)
    return pd.DataFrame(df_containers_dict)


def request_to_excel(request: Request, path: Path) -> None:
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    df_blocks = blocks_to_df(request.blocks)
    df_container = container_to_df(request.container)
    with pd.ExcelWriter(path) as writer:
        df_blocks.to_excel(writer, sheet_name=BLOCK_SHEET, index=False)
        df_container.to_excel(writer, sheet_name=CONTAINER_SHEET, index=False)


def excel_to_request(path: Path) -> Request:
    df_blocks = pd.read_excel(path, sheet_name=BLOCK_SHEET)
    blocks: list[Block] = []
    for idx, row in df_blocks.iterrows():
        name = getattr(row, BLOCK_NAME)
        depth = getattr(row, DEPTH)
        width = getattr(row, WIDTH)
        height = getattr(row, HEIGHT)
        weight = getattr(row, WEIGHT)
        shape = (depth, width, height)
        # random color
        color = (RNG.randint(0, 223), RNG.randint(0, 223), RNG.randint(0, 223))
        stackable = getattr(row, STACKABLE)
        right_side_up = getattr(row, RIGHT_SIDE_UP)
        block = Block(name, shape, weight, color, stackable, right_side_up)
        blocks.append(block)
    df_container = pd.read_excel(path, sheet_name=CONTAINER_SHEET)
    container_shape = (
        df_container.loc[0, DEPTH],
        df_container.loc[0, WIDTH],
        df_container.loc[0, HEIGHT],
    )
    weight_capacity = df_container.loc[0, WEIGHT_CAPACITY]
    container = Container("container", container_shape, weight_capacity)
    return Request(blocks, container)


def corners_to_df(corners: list[Corner]) -> pd.DataFrame:
    df_corners_dict: dict[str, list[float]] = {
        BACK: [],
        LEFT: [],
        BOTTOM: [],
    }
    for corner in corners:
        back, left, bottom = corner
        df_corners_dict[BACK].append(back)
        df_corners_dict[LEFT].append(left)
        df_corners_dict[BOTTOM].append(bottom)
    return pd.DataFrame(df_corners_dict)


def response_to_excel(response: Response, path: Path) -> None:
    df_blocks = blocks_to_df(response.blocks)
    df_corners = corners_to_df(response.corners)
    df = pd.merge(df_blocks, df_corners, left_index=True, right_index=True, how="left")
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name=RESPONSE_SHEET, index=False)
