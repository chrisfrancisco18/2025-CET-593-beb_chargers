import streamlit as st
from beb_chargers.zebra.utils import process_inputs
from beb_chargers.opt.model import ChargerLocationModel

for k, v in st.session_state.items():
    st.session_state[k] = v

if 'gap_pct' not in st.session_state:
    st.session_state.gap_pct = 5
if 'opt_gap' not in st.session_state:
    st.session_state.opt_gap = 0.05
st.markdown(
    '# Run Optimization Models\n'
    'Click the Optimize button below to run the BEB-BRP and BEB-OCL models '
    'that will adjust bus schedules where necessary, identify layover '
    'charging locations, and develop a charging schedule for each bus. If '
    'desired, adjust the advanced options below to set optimization solver '
    'parameters. Otherwise, leave them at the default values.'
)

st.markdown(
    '## Advanced Options\n'
    'Set the optimality gap for the optimization solver here. Optimization '
    'will conclude as soon as the solver finds a solution that is within '
    'the given tolerance of the best possible solution.')

r51, _, _ = st.columns((1, 1, 2))
st.session_state.gap_pct = r51.number_input(
    'Optimality Gap (%)', 0, 100, int(st.session_state.gap_pct))
st.session_state.opt_gap = st.session_state.gap_pct / 100
run_opt_button = st.button('Run Optimization Model')


if run_opt_button:
    process_inputs(
        st.session_state.gtfs, st.session_state.chosen_rts,
        st.session_state.chosen_sites, st.session_state.charge_coords,
        st.session_state.depot_coords, st.session_state.f_s,
        st.session_state.g_s, st.session_state.n_max,
        st.session_state.u_full,
        st.session_state.u_pct, st.session_state.rho_kw,
        st.session_state.energy_rate)
    st.info(
        'Running optimization. This could take anywhere from a few '
        'seconds to several minutes or more, depending on the '
        'parameter values you supplied.')

    flm = ChargerLocationModel(**st.session_state.opt_kwargs)
    flm.solve(alpha=st.session_state.alpha, opt_gap=st.session_state.opt_gap)
    st.session_state.result_df = flm.to_df()
    st.session_state.summary_df = flm.summary_to_df()
    st.success('Optimization complete! View other pages to explore results.')
    st.session_state.results_ready = True
