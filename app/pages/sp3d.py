import streamlit as st

from src.converter import excel_to_request
from src.interface import INF, Image
from src.solver import StripPackingSolver


def score_to_num_unpacked_and_top_height(score: float) -> tuple[int, float]:
    num_unpacked = int(score // INF)
    top_height = score - INF * num_unpacked
    return num_unpacked, top_height


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
num_unpacked_holder = st.empty()
top_height_holder = st.empty()
image_holder = st.empty()
if reset and file is not None:
    request = excel_to_request(file)
    solver = StripPackingSolver(request)
    st.session_state["solver"] = solver
    st.session_state["score"] = solver.opt_score
    st.session_state["image"] = solver.render(size, padding)

try:
    num_unpacked, top_height = score_to_num_unpacked_and_top_height(
        st.session_state["score"]
    )
    num_unpacked_holder.write(f"Number of Unpacked Blocks = {num_unpacked}")
    top_height_holder.write(f"Top Height = {top_height}")
    image_holder.image(st.session_state["image"])
    use_solver: StripPackingSolver = st.session_state["solver"]
    im: Image = st.session_state["image"]
    if calculate:
        stop = col3.button("Stop")
        for score, image in use_solver.loop_render(
            max_iter, allow_rotate, temparature, size, padding
        ):
            num_unpacked, top_height = score_to_num_unpacked_and_top_height(
                st.session_state["score"]
            )
            num_unpacked_holder.write(
                f"Number of Unpacked Blocks = {num_unpacked}"
            )
            top_height_holder.write(f"Top Height = {top_height}")
            image_holder.image(image)
            st.session_state["score"] = score
            st.session_state["image"] = image
            if stop:
                break
except KeyError:
    pass
