import os
import sys
import streamlit as st

CURDIR = os.path.dirname(os.path.abspath(__file__))
PARDIR = os.path.dirname(CURDIR)
sys.path.append(PARDIR)

st.markdown("# Packing Problems")
