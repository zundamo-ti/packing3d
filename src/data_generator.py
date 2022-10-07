import random
from typing import Optional

from src.converter import request_to_excel
from src.interface import Block, Color, Image, Request, Shape


def random_shape(block_size: int, rng: random.Random) -> Shape:
    min_size = block_size // 2
    max_size = 3 * block_size // 2
    return (
        rng.randint(min_size, max_size),
        rng.randint(min_size, max_size),
        rng.randint(min_size, max_size),
    )


def random_color(rng: random.Random) -> Color:
    return (
        rng.randint(0, 255),
        rng.randint(0, 255),
        rng.randint(0, 255),
    )


def generate_request(
    block_size: int,
    n_stackables: int,
    n_unstackables: int, 
    container_shape: tuple[int, int, int],
    seed: Optional[int],
) -> Request:
    data_rng = random.Random(seed)
    blocks = [
        Block(
            f"block{i}",
            random_shape(block_size, data_rng),
            random_color(data_rng),
            stackable=True,
        )
        for i in range(n_stackables)
    ] + [
        Block(
            f"block{i + n_stackables}",
            random_shape(block_size, data_rng),
            random_color(data_rng),
            stackable=False,
        )
        for i in range(n_unstackables)
    ]
    return Request(blocks, container_shape)


if __name__ == "__main__":
    import os
    from argparse import ArgumentParser
    from pathlib import Path

    parser = ArgumentParser()
    parser.add_argument("-b", "--block-size", type=int, default=40)
    parser.add_argument("-s", "--stackable-blocks", type=int, default=10)
    parser.add_argument("-u", "--unstackable-blocks", type=int, default=10)
    parser.add_argument("-c", "--container-shape", nargs=3, type=int, default=(200, 100, 100))
    parser.add_argument("-r", "--random-seed", type=int)
    args = parser.parse_args()
    block_size: int = args.block_size
    n_stackables: int = args.stackable_blocks
    n_unstackables: int = args.unstackable_blocks
    container_shape: tuple[int, int, int] = args.container_shape
    seed: int = args.random_seed if args.random_seed is not None else random.randint(0, 1e9)
    request = generate_request(
        block_size, n_stackables, n_unstackables, container_shape, seed
    )
    DATADIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = DATADIR / Path(f"data/request_{block_size=}_{n_stackables=}_{n_unstackables=}_{container_shape=}_{seed=}.xlsx")
    request_to_excel(request, path)
