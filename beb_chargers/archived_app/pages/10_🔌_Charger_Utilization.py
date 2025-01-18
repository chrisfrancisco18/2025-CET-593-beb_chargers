import streamlit as st
import datetime
from beb_chargers.vis.vis import plot_chargers

for k, v in st.session_state.items():
    st.session_state[k] = v

if not st.session_state.results_ready:
    st.error(
        'You have not generated any results yet. Please run the optimization '
        'to generate results that will be shown here.')
else:
    st.title('Charger Utilization')
    used_sites = st.session_state.result_df[
        'chg_site'].dropna().unique().tolist()
    used_sites = ['All'] + used_sites
    site = st.selectbox('Charging Site', used_sites)
    fig = plot_chargers(
        result_df=st.session_state.result_df,
        zero_time=datetime.datetime(2019, 1, 1, 0),
        site=site)
    st.pyplot(fig)

