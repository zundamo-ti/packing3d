import streamlit as st

from src.bin_packing_solver import (
    BLOCK_UNSTACKED_PENALTY,
    CONTAINER_USED_PENALTY,
    BinPackingSolver,
)
from src.converter import bin_packing_to_json, excel_to_bin_packing_request
from src.interface import INF, Image


def score_to_n_unpacked_and_n_containers_and_container_score(
    score: float,
) -> tuple[int, int, float]:
    n_unpacked = int(score // BLOCK_UNSTACKED_PENALTY)
    score -= BLOCK_UNSTACKED_PENALTY * n_unpacked
    n_containers = int(score // CONTAINER_USED_PENALTY)
    container_score = score - CONTAINER_USED_PENALTY * n_containers
    return n_unpacked, n_containers, container_score


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
container_score_holder = st.empty()
image_holder = st.empty()
if reset and file is not None:
    request = excel_to_bin_packing_request(file)
    solver = BinPackingSolver(request)
    st.session_state["solver"] = solver
    st.session_state["image"] = solver.render(size, padding)
    (
        n_unpacked,
        n_containers,
        container_score,
    ) = score_to_n_unpacked_and_n_containers_and_container_score(
        solver.total_score
    )
    st.session_state["n_unpacked"] = n_unpacked
    st.session_state["n_containers"] = n_containers
    st.session_state["container_score"] = container_score
    n_unpacked_holder.write(
        f"Number of Unpacked Blokcs: {st.session_state['n_unpacked']}"
    )
    n_containers_holder.write(
        f"Number of Used Containers: {st.session_state['n_containers']}"
    )
    container_score_holder.write(
        f"Container Score: {st.session_state['container_score']:.1f}"
    )
    image_holder.image(st.session_state["image"])


try:
    image_holder.image(st.session_state["image"])
    use_solver: BinPackingSolver = st.session_state["solver"]
    to_json = col1.button("Response to JSON string")
    if to_json:
        with open("data/response.json", "w") as f:
            json_str = bin_packing_to_json(
                use_solver.request, use_solver.response, f
            )
    if calculate:
        stop = col3.button("Stop")
        for score, image in use_solver.loop_render(
            max_iter, temparature, size, padding
        ):
            (
                n_unpacked,
                n_containers,
                container_score,
            ) = score_to_n_unpacked_and_n_containers_and_container_score(score)
            st.session_state["n_unpacked"] = n_unpacked
            st.session_state["n_containers"] = n_containers
            st.session_state["container_score"] = container_score
            n_unpacked_holder.write(
                f"Number of Unpacked Blokcs: {st.session_state['n_unpacked']}"
            )
            n_containers_holder.write(
                f"Number of Used Containers: "
                f"{st.session_state['n_containers']}"
            )
            container_score_holder.write(
                f"Container Score: {st.session_state['container_score']:.1f}"
            )
            image_holder.image(image)
            st.session_state["image"] = image
            if stop:
                break
except KeyError as e:
    print(e)
