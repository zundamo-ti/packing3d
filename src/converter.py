import os
import random
from pathlib import Path
from typing import Any

import pandas as pd

from src.interface import Block, Corner, Request, Shape, StripPackingRequest, StripPackingResponse

# sheet names
CONTAINER_SHEET = "container"
BLOCKS_SHEET = "block"
RESPONSE_SHEET = "response"
# column names
NAME = "name_"
DEPTH = "depth"
WIDTH = "width"
HEIGHT = "height"
BACK = "back"
LEFT = "left"
BOTTOM = "bottom"
STACKABLE = "stackable"
RIGHT_SIDE_UP = "right_side_up"
# random seed
RNG = random.Random(0)


def blocks_to_df(blocks: list[Block]) -> pd.DataFrame:
    df_blocks_dict: dict[str, list[Any]] = {
        NAME: [],
        DEPTH: [],
        WIDTH: [],
        HEIGHT: [],
        STACKABLE: [],
        RIGHT_SIDE_UP: [],
    }
    for block in blocks:
        depth, width, height = block.shape
        df_blocks_dict[NAME].append(block.name)
        df_blocks_dict[DEPTH].append(depth)
        df_blocks_dict[WIDTH].append(width)
        df_blocks_dict[HEIGHT].append(height)
        df_blocks_dict[STACKABLE].append(block.stackable)
        df_blocks_dict[RIGHT_SIDE_UP].append(block.right_side_up)
    return pd.DataFrame(df_blocks_dict)


def container_to_df(container_shape: Shape) -> pd.DataFrame:
    depth, width, height = container_shape
    return pd.DataFrame(
        {
            DEPTH: [depth],
            WIDTH: [width],
            HEIGHT: [height],
        }
    )


def request_to_excel(request: StripPackingRequest, path: Path) -> None:
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    df_blocks = blocks_to_df(request.blocks)
    df_container = container_to_df(request.container_shape)
    with pd.ExcelWriter(path) as writer:
        df_blocks.to_excel(writer, sheet_name=BLOCKS_SHEET, index=False)
        df_container.to_excel(writer, sheet_name=CONTAINER_SHEET, index=False)


def excel_to_request(path: Path) -> Request:
    df_blocks = pd.read_excel(path, sheet_name=BLOCKS_SHEET)
    df_container = pd.read_excel(path, sheet_name=CONTAINER_SHEET)
    container_shape = (
        df_container.loc[0, DEPTH],
        df_container.loc[0, WIDTH],
        df_container.loc[0, HEIGHT],
    )
    blocks: list[Block] = []
    for idx, row in df_blocks.iterrows():
        name = getattr(row, NAME)
        depth = getattr(row, DEPTH)
        width = getattr(row, WIDTH)
        height = getattr(row, HEIGHT)
        shape = (depth, width, height)
        # random color
        color = (RNG.randint(0, 223), RNG.randint(0, 223), RNG.randint(0, 223))
        stackable = getattr(row, STACKABLE)
        right_side_up = getattr(row, RIGHT_SIDE_UP)
        block = Block(name, shape, color, stackable, right_side_up)
        blocks.append(block)
    return StripPackingRequest(blocks, container_shape)


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


def response_to_excel(response: StripPackingResponse, path: Path) -> None:
    df_blocks = blocks_to_df(response.blocks)
    df_corners = corners_to_df(response.corners)
    df = pd.merge(df_blocks, df_corners, left_index=True, right_index=True, how="left")
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name=RESPONSE_SHEET, index=False)
