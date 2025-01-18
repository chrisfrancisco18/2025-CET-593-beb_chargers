import streamlit as st
from beb_chargers.zebra.utils import load_locations, load_gtfs
from pathlib import Path

for k, v in st.session_state.items():
    st.session_state[k] = v


def main():
    """Main function to run Streamlit zebra"""
    st.image(str(Path(__file__).resolve().parent / 'iuts_header.png'))
    about_file = Path(__file__).resolve().parent / 'project_overview.md'
    about_text = about_file.read_text()
    st.markdown(about_text)

    depot_coords = (47.495809, -122.286190)
    st.session_state.depot_coords = depot_coords
    # TODO: properly update this attribute when non-defaults are chosen
    st.session_state.locs = load_locations()

    # Load GTFS data
    st.session_state.gtfs = load_gtfs()

    # Initialize empty results
    if 'result_df' not in st.session_state or 'summary_df' not in st.session_state:
        st.session_state.result_df = None
        st.session_state.summary_df = None
        st.session_state.results_ready = False

    # hide upper-right menu
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
