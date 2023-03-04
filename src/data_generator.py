import random
from typing import Optional

from src.interface import (
    Block,
    Color,
    Container,
    Request,
    Shape,
    volume,
)


def random_shape(block_size: float, rng: random.Random) -> Shape:
    min_size = block_size // 2
    max_size = 3 * block_size // 2
    return (
        rng.uniform(min_size, max_size),
        rng.uniform(min_size, max_size),
        rng.uniform(min_size, max_size),
    )


def random_color(rng: random.Random) -> Color:
    return (
        rng.randint(0, 255),
        rng.randint(0, 255),
        rng.randint(0, 255),
    )


def random_block(name: str, block_size: float, stackable: bool, rng: random.Random) -> Block:
    shape = random_shape(block_size, rng)
    volume = shape[0] * shape[1] * shape[2]
    weight = rng.uniform(volume / 2, 3 * volume / 2)
    return Block(name, shape, weight, random_color(rng), stackable)


def random_container(name: str, container_size: float, rng: random.Random) -> Container:
    lower_rate = 0.9
    upper_rate = 1.1
    shape = (
        rng.uniform(2 * container_size * lower_rate, 2 * container_size * upper_rate),
        rng.uniform(container_size * lower_rate, container_size * upper_rate),
        rng.uniform(container_size * lower_rate, container_size * upper_rate),
    )
    volume = shape[0] * shape[1] * shape[2]
    weight_capacity = rng.uniform(volume / 2, 3 * volume / 2)
    return Container(name, shape, weight_capacity)


def generate_strip_packing_request(
    block_size: int,
    n_stackables: int,
    n_unstackables: int,
    container_shape: tuple[int, int, int],
    seed: Optional[int],
) -> Request:
    data_rng = random.Random(seed)
    blocks = [
        random_block(f"block{i + 1}", block_size, True, data_rng) for i in range(n_stackables)
    ] + [
        random_block(f"block{i + n_stackables + 1}", block_size, False, data_rng)
        for i in range(n_unstackables)
    ]
    container_volume = volume(container_shape)
    weight_capacity = data_rng.uniform(container_volume / 2, 3 * container_volume / 2)
    container = Container("container", container_shape, weight_capacity)
    return Request(blocks, container)


if __name__ == "__main__":
    import os
    from pathlib import Path

    from src.converter import request_to_excel

    DATADIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    seed: int = random.Random().randint(0, 1_000_000_000)
    request = generate_strip_packing_request(
        block_size=40, container_shape=(200, 100, 100), n_stackables=15, n_unstackables=5, seed=seed
    )
    path = DATADIR / Path(f"data/request_{seed=}.xlsx")
    request_to_excel(request, path)
