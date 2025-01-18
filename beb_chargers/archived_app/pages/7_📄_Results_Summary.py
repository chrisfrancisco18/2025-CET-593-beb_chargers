import streamlit as st
from millify import millify
import pandas as pd
from beb_chargers.vis.vis import plot_charging_and_dh_comparison

for k, v in st.session_state.items():
    st.session_state[k] = v

st.title("BEB Charger Optimization Summary")

if st.session_state.results_ready:
    results = st.session_state.result_df
    summary = st.session_state.summary_df

    # Objective cost components
    st.header('Costs')
    row1_0, row1_1 = st.columns(2)
    row1_0.metric(
        label='Capital Cost ($)',
        value=millify(summary.at[0, 'capital_cost'], precision=3,
                      drop_nulls=False))
    row1_0.caption(
        'Capital cost includes all costs associated with setting up sites '
        'for chargers, plus purchasing and installing chargers.'
    )
    row1_1.metric(
        label='Deadhead Cost ($)',
        value=millify(summary.at[0, 'operations_cost'], precision=3,
                      drop_nulls=False))
    row1_1.caption(
        'Deadhead cost reflects the cost of increased bus operation time due '
        'to deadheading to and from chargers.'
    )

    # Number of chargers at each site
    n_cols = [c for c in summary.columns if c[:4] == 'N at']
    df_cols = summary[n_cols].T
    df_cols = df_cols[df_cols[0] > 0]
    df_cols = df_cols.rename({s: s[4:] for s in df_cols.index})
    df_cols[0] = df_cols[0].astype(int)
    df_cols.columns = ['Number of Chargers Built']
    st.header('Chargers At Each Site')
    st.table(df_cols)

    # Summary values
    st.header('Key Outputs')
    num_bus = len(pd.unique(results['block_id'].dropna()))
    num_chg_visits = (results['chg_time'].dropna() > 1e-6).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Number of Backup Buses Required",
                value=int(summary.at[0, 'n_backups']))
    col2.metric(label="Number of Buses Charging",
                value=num_bus, delta=None, delta_color="off")

    results['dh_net'] = results['dh1'] + results['dh2'] - results['dh3']
    sum_net = results['dh_net'].sum()
    mean_net = sum_net / sum(~pd.isna(results['chg_site']))
    mean_chg = results['chg_time'].sum() / num_chg_visits

    chg_summary_str = \
        'In total, **:blue[{} buses need to charge]** at some point during the specified ' \
        'service day. These buses charge a total of {} times (**:blue[{:.2f} charger ' \
        'visits per bus]**). On average, **:blue[deadheading to and from a charger takes ' \
        '{:.2f} minutes]** longer than deadheading straight to the start of the ' \
        'next trip, and :blue[**the average time a bus spends plugged in is ' \
        '{:.2f} minutes**].'.format(
            num_bus, num_chg_visits, num_chg_visits / num_bus, mean_net,
            mean_chg)
    st.markdown(chg_summary_str)

else:
    st.error(
        'You have not generated any results yet. Please run the optimization to generate'
        ' results that will be shown here.')

st.markdown('## Charging and Deadhead Behavior')
if st.session_state.results_ready:
    ch_dh_fig = plot_charging_and_dh_comparison(st.session_state.result_df)
    st.plotly_chart(ch_dh_fig)
else:
    st.error(
        'You have not generated any results yet. Please run the optimization '
        'to generate results that will be shown here.')
