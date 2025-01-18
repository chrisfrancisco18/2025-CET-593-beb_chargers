import streamlit as st
from beb_chargers.vis.vis import plot_deadhead

for k, v in st.session_state.items():
    st.session_state[k] = v

if st.session_state.results_ready:
    dh_results = st.session_state.result_df.copy()
    # dh_results = dh_results[~dh_results['trip_id'].isin([0, 100])]
    # try:
    #     dh_results['term_lat_lon'] = dh_results.apply(
    #         lambda x: coords.at[x['trip_id'], 'term_lat_lon'], axis=1)
    # except ValueError:
    #     st.dataframe(coords)
    #     st.dataframe(dh_results)
    # dh_results['term_y'] = dh_results.apply(
    #     lambda x: x['term_lat_lon'][0], axis=1)
    # dh_results['term_x'] = dh_results.apply(
    #     lambda x: x['term_lat_lon'][1], axis=1)
    # chg_cts = pd.DataFrame(dh_results.groupby(
    #     ['term_x', 'term_y', 'chg_site']).count()['trip_id']).reset_index()
    # chg_cts = chg_cts.rename({'trip_id': 'n_trips'}, axis=1)
    # chg_cts['chg_y'] = chg_cts.apply(
    #     lambda x: locs.at[x['chg_site'], 'y'], axis=1)
    # chg_cts['chg_x'] = chg_cts.apply(
    #     lambda x: locs.at[x['chg_site'], 'x'], axis=1)

    # used_stations = list(chg_cts['chg_site'].unique())
    # used_loc_df = locs.filter(items=used_stations, axis=0)
    fig = plot_deadhead(
        result_df=dh_results, loc_df=st.session_state.locs,
        coords_df=st.session_state.all_trips_df.set_index('trip_id'))
    fig.write_html('deadhead_plot.html')
    st.plotly_chart(fig)

else:
    st.error(
        'You have not generated any results yet. Please run the optimization '
        'to generate results that will be shown here.')