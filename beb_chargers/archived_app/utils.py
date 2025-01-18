from pathlib import Path
from beb_chargers.data import GTFSData
from beb_chargers.opt.model import ChargerLocationModel
import datetime
import pandas as pd
import streamlit as st


@st.cache_data
def load_gtfs():
    """Load GTFS data and let Streamlit handle caching."""
    path_here = Path(__file__).absolute()
    gtfs_path = path_here.parent.parent / 'data' / 'gtfs'
    return GTFSData.from_dir(str(gtfs_path))


@st.cache_data
def load_locations():
    """
    Load default candidate charger locations from .csv file
    (this file is included in the repo)
    """
    path_here = Path(__file__).absolute()
    locs_path = path_here.parent.parent / 'data' / 'all_king_cty_sites.csv'
    locs = pd.read_csv(str(locs_path))
    locs['symbol'] = 'fuel'
    return locs.set_index('name')


@st.cache_data(show_spinner=False)
def process_inputs(
        _gtfs, chosen_rts, chosen_sites, charge_coords, depot_coords, f_s, g_s,
        n_max, u_full, u_pct, rho_kw, energy_rate):
    # Go from route names to route IDs
    matching_routes = _gtfs.filter_df(
        _gtfs.routes_df, 'route_short_name', chosen_rts)
    route_ids = set(matching_routes.index)

    # Consider all unique blocks that involve these routes
    ref_date = datetime.datetime(2020, 3, 9)
    sid_trips = _gtfs.get_trips_from_sids(86021)
    all_trips_df = _gtfs.filter_df(sid_trips, 'route_id', route_ids)
    all_trips_df = _gtfs.add_trip_data(all_trips_df, ref_date)
    st.session_state.all_trips_df = all_trips_df
    all_blocks = all_trips_df['block_id'].unique().tolist()

    # Create dict of inputs to BEBModel
    # Build inputs for optimization
    opt_kwargs = _gtfs.build_opt_inputs(
        all_blocks, all_trips_df, chosen_sites,
        charge_coords, depot_coords)

    charge_nodes = st.session_state.chosen_sites
    fixed_costs = {s: f_s for s in charge_nodes}
    max_ch = {s: n_max for s in charge_nodes}
    bus_caps = {b: u_full * u_pct / 100
                for b in all_blocks}
    charger_rates = {s: rho_kw / 60 for s in charge_nodes}
    energy_rates = {
        k: energy_rate for k in opt_kwargs['veh_trip_pairs']}

    # Create full dict of optimization inputs
    opt_kwargs['vehicles'] = all_blocks
    opt_kwargs['chg_sites'] = charge_nodes
    opt_kwargs['chg_lims'] = bus_caps
    opt_kwargs['chg_rates'] = charger_rates
    opt_kwargs['energy_rates'] = energy_rates
    opt_kwargs['site_costs'] = fixed_costs
    opt_kwargs['charger_costs'] = {
        s: g_s for s in charge_nodes}
    opt_kwargs['max_chargers'] = max_ch
    opt_kwargs['depot_coords'] = depot_coords
    opt_kwargs['trips_df'] = all_trips_df
    if 'opt_kwargs' not in st.session_state:
        st.session_state.opt_kwargs = dict()
    st.session_state.opt_kwargs = opt_kwargs
    st.session_state.model = ChargerLocationModel(**opt_kwargs)

