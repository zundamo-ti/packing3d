import random

import streamlit as st

from models.sp3d.interface import Request
from models.sp3d.solver import Solver

with st.sidebar:
    container_depth = float(
        st.number_input("Container Depth", min_value=0.0, value=100.0, step=1.0)
    )
    container_width = float(
        st.number_input("Container Width", min_value=0.0, value=100.0, step=1.0)
    )
    container_height = float(
        st.number_input("Container Height", min_value=0.0, value=100.0, step=1.0)
    )
    container_shape = (container_depth, container_width, container_height)

rng = random.Random()
request = Request(container_shape, [])
solver = Solver(request, rng)


image_holder = st.empty()
image = solver.render(size=700)
image_holder.image(image)
