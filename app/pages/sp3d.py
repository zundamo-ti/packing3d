import random

import cv2
import streamlit as st

from models.sp3d.interface import Block, Color, Image, Request, Shape
from models.sp3d.solver import Solver


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


with st.sidebar:
    data_seed = int(st.number_input("Data Seed", value=0))
    container_depth = float(
        st.number_input(
            "Container Depth", min_value=0.0, value=200.0, step=10.0
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
    n_blocks = int(
        st.number_input("Number of Blocks", min_value=1, step=1, value=20)
    )
    block_size = int(
        st.number_input(
            "Block Size",
            min_value=20,
            max_value=int(container_min),
            value=40,
            step=10,
        )
    )
    max_iter = int(st.number_input("Max Iteration", min_value=1, value=1000))
    temparature = float(
        st.number_input("Temparature", min_value=0.0, value=0.0, step=1.0)
    )
    container_shape = (container_depth, container_width, container_height)
    container_volume = container_depth * container_width * container_height

size = 700
padding = 20

col1, col2, col3 = st.columns(3)
reset = col1.button("Reset")
calculate = col2.button("Calculate")
pf_holder = st.empty()
score_holder = st.empty()
image_holder = st.empty()
if "image" not in st.session_state or reset:
    data_rng = random.Random(data_seed)
    blocks = [
        Block(
            f"block{i}",
            random_shape(block_size, data_rng),
            random_color(data_rng),
        )
        for i in range(n_blocks)
    ]
    total_volume = sum(block.volume for block in blocks)
    request = Request(container_shape, blocks)
    solver = Solver(request, temparature)
    st.session_state["solver"] = solver
    st.session_state["score"] = solver.opt_score
    st.session_state["image"] = solver.render(size, padding)
    st.session_state["packing_factor"] = total_volume / container_volume

packing_factor: float = st.session_state["packing_factor"]
pf_holder.write(f"packing factor = {int(1000 * packing_factor) / 10} %")
score_holder.write(f"optimal score = {st.session_state['score']}")
image_holder.image(st.session_state["image"])
use_solver: Solver = st.session_state["solver"]
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
im: Image = st.session_state["image"]
writer = cv2.VideoWriter("./movie.mp4", fourcc, 20.0, im.shape[:2][::-1])
if calculate:
    stop = col3.button("Stop")
    for score, image in use_solver.loop(max_iter, size, padding):
        score_holder.write(f"optimal score = {score}")
        image_holder.image(image)
        writer.write(image)
        st.session_state["score"] = score
        st.session_state["image"] = image
        if stop:
            break
