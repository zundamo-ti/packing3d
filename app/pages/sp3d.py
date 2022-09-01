import random

import cv2
import streamlit as st

from models.sp3d.interface import Block, Color, Image, Request, Shape
from models.sp3d.solver import Solver


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


with st.sidebar:
    container_depth = float(
        st.number_input(
            "Container Depth", min_value=0.0, value=150.0, step=10.0
        )
    )
    container_width = float(
        st.number_input(
            "Container Width", min_value=0.0, value=100.0, step=10.0
        )
    )
    container_height = float(
        st.number_input(
            "Container Height", min_value=0.0, value=100.0, step=10.0
        )
    )
    container_min = min(container_depth, container_width, container_height)
    n_blocks = int(st.number_input("Number of Blocks", min_value=10, step=1))
    block_size = float(
        st.number_input(
            "Block Size", min_value=20.0, max_value=container_min, value=40.0, step=10.0
        )
    )
    max_iter = int(st.number_input("Max Iteration", min_value=1, value=100))
    container_shape = (container_depth, container_width, container_height)

size = 700
padding = 20

col1, col2, col3 = st.columns(3)
reset = col1.button("Reset")
calculate = col2.button("Calculate")
image_holder = st.empty()
if "image" not in st.session_state or reset:
    rng = random.Random()
    blocks = [
        Block(f"block{i}", random_shape(block_size, rng), random_color(rng))
        for i in range(n_blocks)
    ]
    request = Request(container_shape, blocks)
    solver = Solver(request)
    image = solver.render(size, padding)
    st.session_state["solver"] = solver
    st.session_state["image"] = image

image_holder.image(st.session_state["image"])
use_solver: Solver = st.session_state["solver"]
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
image: Image = st.session_state["image"]
writer = cv2.VideoWriter("./movie.mp4", fourcc, 20.0, image.shape[:2][::-1])
if calculate:
    stop = col3.button("Stop")
    for image in use_solver.loop(max_iter, size, padding):
        image_holder.image(image)
        writer.write(image)
        st.session_state["image"] = image
        if stop:
            break
