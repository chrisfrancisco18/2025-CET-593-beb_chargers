import streamlit as st

for k, v in st.session_state.items():
    st.session_state[k] = v

st.markdown(
    '# Technology Inputs\nUse this pages to set technology parameters for the '
    'charger location models, including information about project costs, '
    'charger details, and bus specifications.'
)

# Set the defaults for session state and implement reset
_, ctr, _ = st.columns((1, 1, 1))
tech_reset = ctr.button('Restore Defaults')

# Handle default values of all technology parameters
tech_defaults = {
    'rho_kw': 300,
    'hr_cost': 80,
    'chg_life': 12,
    'u_pct': 75,
    'u_full': 466,
    'f_s': 2e5,
    'g_s': 7e5,
    'alpha': 50 * 10 * 365 / 60,
    'energy_rate': 3.0
}

for tech_param in tech_defaults:
    if tech_param not in st.session_state or tech_reset:
        st.session_state[tech_param] = tech_defaults[tech_param]

# Allow user to configure some of the model's input parameters
st.subheader('Finances')
r01, r02, r03 = st.columns((1, 1, 1))
r01.number_input(
    "Site Cost ($)", 0, 10000000, key='f_s')
r02.number_input(
    "Deadhead Time Cost ($/hr)", 0, 1000, key='hr_cost')
r03.number_input(
    "Planning Lifespan (years)", 0, 20, key='chg_life')
st.session_state.alpha = st.session_state.hr_cost * 365 \
    * st.session_state.chg_life / 60

st.markdown(
    '### Technology \n'
    'Use the following inputs to provide details about the chargers you '
    'are considering and the batteries on electric buses in your system.')
# Inputs to specify charger options for purchase/install
st.markdown('#### Charger Options')
r12, r13 = st.columns((1, 1))
r12.number_input(
    'Charger Power Output (kW)', 50, 1000, key='rho_kw')
r13.number_input(
    'Purchase + Install Cost ($)', 0, 3000000, key='g_s')

st.markdown('#### Battery Details')
r41, r42, r43 = st.columns(3)
r42.number_input(
    'Usable Battery Capacity (%)', 0, 100,
    key='u_pct')
r41.number_input(
    'Battery Capacity (kWh)', 60, 800, key='u_full')
r43.number_input(
    'Energy Consumption Rate (kWh/mi)', 0.5, 4.0, step=0.1, key='energy_rate')
