import streamlit as st
from beb_chargers.vis.vis import plot_trips_and_terminals
from beb_chargers.zebra.utils import process_inputs

for k, v in st.session_state.items():
    st.session_state[k] = v

process_inputs(
    st.session_state.gtfs, st.session_state.chosen_rts,
    st.session_state.chosen_sites, st.session_state.charge_coords,
    st.session_state.depot_coords, st.session_state.f_s,
    st.session_state.g_s, st.session_state.n_max, st.session_state.u_full,
    st.session_state.u_pct, st.session_state.rho_kw,
    st.session_state.energy_rate)

st.markdown(
    '# BEB System Overview\n'
    'The map below shows an overview of the BEB system under study. It shows '
    'all candidate charging locations, plus information about all trips on '
    'charging blocks: both the paths of those trips (shown in red) and the '
    'terminals of those trips. The size of each blue marker scales with the '
    'number of trips that start or end there. Inspecting this map provides '
    'some intuition about what we expect our solution to look like -- we will '
    'probably want to install chargers at sites that are close to where many '
    'trips start and end so that minimal deadheading is required. **The map** '
    '**is interactive!** You can pan around the map and zoom in and out to '
    'see more detail. Hover over a blue terminal marker to see how many trips '
    'start and end there.'
)


# Map trips and terminals (layover blocks only)
lo_blocks = [
    int(v) for v in st.session_state.model.charging_vehs
    if v not in st.session_state.model.infeas_vehs]
all_trips_df = st.session_state.all_trips_df
layover_trips_df = all_trips_df[all_trips_df['block_id'].isin(lo_blocks)]
used_locs = st.session_state.locs.reset_index()
used_locs = used_locs[used_locs['name'].isin(st.session_state.chosen_sites)]
inst_map = plot_trips_and_terminals(
    trips_df=layover_trips_df, locs_df=used_locs,
    shapes_df=st.session_state.gtfs.shapes_df)
st.plotly_chart(inst_map)

