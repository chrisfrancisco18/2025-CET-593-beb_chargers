import streamlit as st
import pandas as pd

for k, v in st.session_state.items():
    st.session_state[k] = v

st.markdown(
    '# Geographic Inputs\nUse this page to set geographic inputs for the '
    'charger location models, including candidate charging locations, maximum '
    'number of chargers per site, bus depot location, and which bus routes to '
    'serve with BEBs. Together, these define the full geographic scope of the '
    'project.'
)

# Charging Site Locations Inputs
st.markdown(
    '### Potential Charging Site Locations \n'
    'Select from the following locations to include '
    'in the analysis OR upload locations from .csv file.')

# Read in necessary data
# trc_sites = pd.read_csv('../data/king_cty_sites_trc.csv')
default_sites = sorted(st.session_state.locs.index.tolist())
if 'chosen_sites' not in st.session_state:
    st.session_state.chosen_sites = default_sites

# Convert column data to list
site_list = sorted(st.session_state.locs.index.tolist())
st.multiselect(
    'Select Charging Sites to Consider',
    options=site_list, key='chosen_sites')

if not st.session_state.chosen_sites:
    st.markdown(
        '#### [Optional] Upload Charging Site Locations .csv File\n'
        'Choose .csv to upload. Column headers must be as follows: '
        'name, label_name, y (lat), x (long)')
    # Allow user to upload .csv of locations
    loc_list_file = st.file_uploader('Choose a file')
    if loc_list_file is not None:
        # Convert file to dataframe:
        user_loc_df = pd.read_csv(loc_list_file)
        if st.checkbox('Show raw data'):
            st.write(user_loc_df)
else:
    st.info('Clear checkboxes to upload a .csv file.')

if 'n_max' not in st.session_state:
    st.session_state.n_max = 10

st.number_input(
    'Maximum Chargers per Site', min_value=1, max_value=20, step=1, key='n_max')

st.session_state.charge_coords = dict()
for n in st.session_state.chosen_sites:
    subdf = st.session_state.locs.loc[n]
    st.session_state.charge_coords[n] = (
        float(subdf['y']), float(subdf['x']))

# Depot Coordinates Inputs
st.markdown(
    '### Depot Location \n'
    'Select the depot location OR enter depot coordinates manually.')
sb_coords = (47.495809, -122.286190)
if 'depot_coords' not in st.session_state:
    st.session_state.depot_coords = sb_coords

# A bit of a hack to preserve manually entered coords, because the
# selectbox default is the first entry.
depot_loc = ['South Base', 'Enter Manually']
if st.session_state.depot_coords != sb_coords:
    depot_loc = ['Enter Manually', 'South Base']
depot_loc_input = st.selectbox(
    'Depot Location', options=depot_loc)

if depot_loc_input == 'South Base':
    st.session_state.depot_coords = sb_coords
    st.info('Select "Enter Manually" to customize depot coordinates.')

if depot_loc_input == 'Enter Manually':
    st.markdown(
        '#### [Optional] Enter Depot Coordinates\n'
        'Use decimal degrees (DD) format.')
    # Allow user to enter depot coordinates manually
    depot_lat_input = st.text_input(
        'Latitude', st.session_state.depot_coords[0])
    depot_long_input = st.text_input(
        'Longitude', st.session_state.depot_coords[1])
    # Assign depot input to tuple
    try:
        st.session_state.depot_coords = (
            float(depot_lat_input), float(depot_long_input))
    except ValueError:
        if depot_lat_input != '' and depot_long_input != '':
            st.error(
                'Input not recognized. Use decimal degrees.')

# Bus Routes Inputs
st.markdown(
    '### Bus routes to consider for electrification. Defaults are the '
    'planned initial BEB routes in South King County.')
default_rts = [101, 102, 111, 116, 143, 150, 157, 158, 159, 177, 178, 179,
               180, 190, 192, 193, 197]
default_rts = [str(r) for r in default_rts]

# if 'chosen_rts' not in st.session_state:
#     st.session_state.chosen_rts = default_rts

rt_choices = sorted(
    set(st.session_state.gtfs.routes_df[
            st.session_state.gtfs.routes_df['route_type'] == 3][
            'route_short_name'].tolist()))
st.multiselect(
    'Select Bus Routes', rt_choices, key='chosen_rts')

