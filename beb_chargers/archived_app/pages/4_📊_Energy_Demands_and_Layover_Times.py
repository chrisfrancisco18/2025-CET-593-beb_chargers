import streamlit as st
from beb_chargers.zebra.utils import process_inputs
from beb_chargers.vis.vis import plot_energy_needs, plot_layover_times

for k, v in st.session_state.items():
    st.session_state[k] = v

st.markdown(
    '# Energy Demands and Layover Times\n'
    'This page shows the results of some initial processing on the bus system '
    'you have specified in the Input pages. Once we have identified which '
    'blocks are feasible without any layover charging ("Non-Charging Blocks") '
    'and which will require layover charging or schedule revisions ("Charging '
    'Blocks"), we identify the total energy consumption of each block (left '
    'plot) and the scheduled layover time after each trip on all blocks '
    '(right plot). If we see that charging blocks have many trips with '
    'abundant layover time, this suggests that layover charging may be '
    'an effective strategy for this system. To see the full system '
    'performance that would result from layover charging, continue through '
    'to run the model via the Optimize page.'
)
process_inputs(
    st.session_state.gtfs, st.session_state.chosen_rts,
    st.session_state.chosen_sites, st.session_state.charge_coords,
    st.session_state.depot_coords, st.session_state.f_s,
    st.session_state.g_s, st.session_state.n_max, st.session_state.u_full,
    st.session_state.u_pct, st.session_state.rho_kw,
    st.session_state.energy_rate)

lcol, rcol = st.columns(2)

with lcol:
    energy_fig = plot_energy_needs(st.session_state.model)
    st.pyplot(energy_fig)

with rcol:
    layover_fig = plot_layover_times(st.session_state.model)
    st.pyplot(layover_fig)
