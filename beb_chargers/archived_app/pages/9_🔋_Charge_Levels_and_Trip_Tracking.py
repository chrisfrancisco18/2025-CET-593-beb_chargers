import streamlit as st
from beb_chargers.vis.vis import plot_bus_soc, plot_one_trip

for k, v in st.session_state.items():
    st.session_state[k] = v

if not st.session_state.results_ready:
    st.error(
        'You have not generated any results yet. Please run the optimization '
        'to generate results that will be shown here.')
else:
    block_id = st.session_state.result_df['block_id'].unique().tolist()
    selected_block = st.selectbox(
        'Block ID', options=block_id,
        help='Block ID refers to a specific set of trips that a single vehicle'
             ' will cover.')
    st.markdown(
        'Plots the battery level of a bus over the course of the day.')
    # TODO: set lower and upper SoC limits separately
    soc_lb = 0
    soc_ub = st.session_state.u_pct / 100
    fig = plot_bus_soc(
        result_df=st.session_state.result_df, block_id=selected_block,
        capacity=st.session_state.u_full, soc_lb=soc_lb, soc_ub=soc_ub)
    st.pyplot(fig)

    t_idxs = st.session_state.result_df[
        st.session_state.result_df['block_id'] == selected_block]['trip_idx']
    selected_trip = st.select_slider('Trip Number', sorted(t_idxs))

    # c1, c2 = st.columns(2)
    fig1, fig2 = plot_one_trip(
        st.session_state.result_df, st.session_state.locs,
        st.session_state.gtfs, selected_block, selected_trip,
        st.session_state.depot_coords)
    fig_to_plot = st.selectbox(
        'Passenger Trip or Deadhead?', ['Passenger Trip', 'Deadhead'])
    if fig_to_plot == 'Passenger Trip':
        st.plotly_chart(fig1)
    else:
        st.plotly_chart(fig2)