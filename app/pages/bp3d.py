import streamlit as st

from src.binpacking_solver import (
    BLOCK_UNSTACKED_PENALTY,
    CONTAINER_USED_PENALTY,
    BinPackingSolver,
)
from src.converter import excel_to_bin_packing_request
from src.interface import INF, Image


def score_to_n_unpacked_and_n_containers_and_top_height(
    score: float,
) -> tuple[int, int, float]:
    n_unpacked = int(score // BLOCK_UNSTACKED_PENALTY)
    score -= BLOCK_UNSTACKED_PENALTY * n_unpacked
    n_containers = int(score // CONTAINER_USED_PENALTY)
    top_height = score - CONTAINER_USED_PENALTY * n_containers
    return n_unpacked, n_containers, top_height


with st.sidebar:
    file = st.file_uploader("Upload File")
    allow_rotate = st.checkbox("Allow Rotate", True)
    max_iter = int(st.number_input("Max Iteration", min_value=1, value=10000))
    temparature = float(
        st.number_input("Temparature", min_value=0.0, value=0.0, step=1.0)
    )

size = 750
padding = 20

col1, col2, col3 = st.columns(3)
reset = col1.button("Reset")
calculate = col2.button("Calculate")
pf_holder = st.empty()
n_unpacked_holder = st.empty()
n_containers_holder = st.empty()
top_height_holder = st.empty()
image_holder = st.empty()
if reset and file is not None:
    request = excel_to_bin_packing_request(file)
    solver = BinPackingSolver(request)
    st.session_state["solver"] = solver
    st.session_state["image"] = solver.render(size, padding)
    (
        n_unpacked,
        n_containers,
        top_height,
    ) = score_to_n_unpacked_and_n_containers_and_top_height(solver.total_score)
    st.session_state["n_unpacked"] = n_unpacked
    st.session_state["n_containers"] = n_containers
    st.session_state["top_height"] = top_height
    n_unpacked_holder.write(
        f"Number of Unpacked Blokcs: {st.session_state['n_unpacked']}"
    )
    n_containers_holder.write(
        f"Number of Used Containers: {st.session_state['n_containers']}"
    )
    top_height_holder.write(f"Top Height: {st.session_state['top_height']}")
    image_holder.image(st.session_state["image"])


try:
    n_unpacked_holder.write(
        f"Number of Unpacked Blokcs: {st.session_state['n_unpacked']}"
    )
    n_containers_holder.write(
        f"Number of Used Containers: {st.session_state['n_containers']}"
    )
    top_height_holder.write(f"Top Height: {st.session_state['top_height']}")
    image_holder.image(st.session_state["image"])
    use_solver: BinPackingSolver = st.session_state["solver"]
    if calculate:
        stop = col3.button("Stop")
        for score, image in use_solver.loop_render(
            max_iter, temparature, size, padding
        ):
            print(f"{score=}")
            (
                n_unpacked,
                n_containers,
                top_height,
            ) = score_to_n_unpacked_and_n_containers_and_top_height(score)
            st.session_state["n_unpacked"] = n_unpacked
            st.session_state["n_containers"] = n_containers
            st.session_state["top_height"] = top_height
            n_unpacked_holder.write(
                f"Number of Unpacked Blokcs: {st.session_state['n_unpacked']}"
            )
            n_containers_holder.write(
                f"Number of Used Containers: "
                f"{st.session_state['n_containers']}"
            )
            top_height_holder.write(
                f"Top Height: {st.session_state['top_height']}"
            )
            image_holder.image(image)
            st.session_state["image"] = image
            if stop:
                break
except KeyError as e:
    print(e)
    pass
