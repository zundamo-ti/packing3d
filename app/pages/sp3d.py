import random

import streamlit as st

from models.sp3d.interface import Block, Request
from models.sp3d.solver import Solver

with st.sidebar:
    container_depth = float(
        st.number_input(
            "Container Depth", min_value=0.0, value=300.0, step=1.0
        )
    )
    container_width = float(
        st.number_input(
            "Container Width", min_value=0.0, value=150.0, step=1.0
        )
    )
    container_height = float(
        st.number_input(
            "Container Height", min_value=0.0, value=150.0, step=1.0
        )
    )
    container_shape = (container_depth, container_width, container_height)

rng = random.Random()
request = Request(container_shape, [])
solver = Solver(request, rng)
solver.blocks = [
    Block("block1", (30, 40, 50), (0, 0, 255)),
    Block("block2", (40, 30, 40), (0, 255, 0)),
    Block("block2", (40, 40, 30), (255, 0, 0)),
]
solver.corners = [
    (0.0, 0.0, 0.0),
    (0.0, 40.0, 0.0),
    (30.0, 0.0, 0.0),
]


image_holder = st.empty()
image = solver.render(size=700)
image_holder.image(image)
