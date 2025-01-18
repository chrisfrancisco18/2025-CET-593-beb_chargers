import pandas as pd
import datetime
import os

# This code is adapted from the Jupyter notebook
# "Final March 2024 data cleaning"


def get_trip_realtime(realtime_df, tid, min_time=None, max_time=None):
    """
    Get the realtime data associated with the given vehicle ID
    within the time range [min_time, max_time].
    """
    t_df = realtime_df[realtime_df['trip_id'] == tid]
    if min_time is not None:
        t_df = t_df[t_df['locationtime'] >= min_time]
    if max_time is not None:
        t_df = t_df[t_df['locationtime'] <= max_time]

    return t_df.sort_values(by='locationtime')


def summarize_realtime_trips(rt_df):
    clean_count = 0
    error_count = 0
    dates = list()
    tids = list()
    start_times = list()
    end_times = list()
    start_delays = list()
    end_delays = list()
    veh_ids = list()
    sort_by = 'locationtime'
    all_dates = rt_df['date'].unique()
    trip_ct = 0
    for d in all_dates:
        d_df = rt_df[rt_df['date'] == d]
        all_trips = d_df['trip_id'].unique()
        for t in all_trips:
            trip_ct += 1
            if trip_ct % 1000 == 0:
                print(f'cleaned {trip_ct} trips')
            t_df = d_df[d_df['trip_id'] == t].sort_values(by=sort_by)

            # Exclude temporal outliers with interquantile filter
            q1 = t_df['locationtime'].quantile(.25)
            q3 = t_df['locationtime'].quantile(.75)
            iqr = q3 - q1
            t_df = t_df[
                t_df['locationtime'].between(
                    q1 - 0.75 * iqr,
                    q3 + 0.75 * iqr
                )
            ]

            # Another IQR filter for schedule deviation
            q1 = t_df['scheduleDeviation'].quantile(.25)
            q3 = t_df['scheduleDeviation'].quantile(.75)
            iqr = q3 - q1
            t_df = t_df[
                t_df['scheduleDeviation'].between(
                    q1 - 1.5 * iqr,
                    q3 + 1.5 * iqr
                )
            ]

            # Exclude all data that includes big negative schedule deviations
            t_df = t_df[t_df['scheduleDeviation'] > -900]

            try:
                t_df = t_df.sort_values(by=['stop_sequence', 'locationtime'])
                first_stop_df = t_df.groupby('nextStop').tail(1).iloc[0]
                first_stop_delay = first_stop_df['scheduleDeviation']
                first_recorded_time = first_stop_df['locationtime']
                veh_id = first_stop_df['vehicle_id']
                last_recorded_time = t_df.groupby('nextStop').head(1).iloc[-1][
                    'locationtime']
                last_stop_delay = t_df.groupby('nextStop').head(1).iloc[-1][
                    'scheduleDeviation']

                start_times.append(first_recorded_time)
                end_times.append(last_recorded_time)
                start_delays.append(first_stop_delay)
                end_delays.append(last_stop_delay)
                veh_ids.append(veh_id)
                tids.append(t)
                dates.append(d)
                clean_count += 1

            except IndexError as e:
                # We end up here if the DF is empty after filtering
                error_count += 1

    rt_trip_summary = pd.DataFrame(
        {
            'date': dates,
            'vehicle_id': veh_ids,
            'trip_id': tids,
            'first_recorded_time': start_times,
            'last_recorded_time': end_times,
            'delay_at_start': start_delays,
            'delay_at_end': end_delays
        }
    ).sort_values(by=['vehicle_id', 'first_recorded_time'])

    # Only include trips at least 10 minutes long
    rt_trip_summary['recorded_duration'] = rt_trip_summary[
                                               'last_recorded_time'] - \
                                           rt_trip_summary[
                                               'first_recorded_time']
    rt_trip_summary = rt_trip_summary[
        rt_trip_summary['recorded_duration'].dt.total_seconds() > 600]

    return rt_trip_summary


def clean_realtime_data(rt_trip_summary, realtime_df):
    """
    Remove data outside the bounds identified in rt_trip_summary
    from realtime_df
    """
    # This code is clunky and slow, but gets the job done
    trip_dfs = list()
    trip_summary = rt_trip_summary.set_index(['date', 'trip_id'])
    for ix in trip_summary.index:
        t_df = get_trip_realtime(
            realtime_df, ix[1], trip_summary.loc[ix, 'first_recorded_time'],
            trip_summary.loc[ix, 'last_recorded_time']
        )

        # Run IQR filter again on cleaned data
        q1 = t_df['locationtime'].quantile(.25)
        q3 = t_df['locationtime'].quantile(.75)
        iqr = q3 - q1
        t_df = t_df[
            t_df['locationtime'].between(
                q1 - 0.75 * iqr,
                q3 + 0.75 * iqr
            )
        ]
        trip_dfs.append(t_df)

    rt_cleaned = pd.concat(trip_dfs).sort_values(by='locationtime')
    return rt_cleaned


def load_chargepoint_data():
    # Read in ChargePoint/ViriCiti data¶
    vc_file = '../beb_chargers/data/viriciti/mar24_energy_data.csv'
    vc_df = pd.read_csv(vc_file)
    vc_df = vc_df.astype(
        dtype={
            'Name': str,
            'ISO Time': str
        }
    )
    # Convert time column to datetime and make sure it's the right time zone
    vc_df['ISO Time'] = pd.to_datetime(
        vc_df['ISO Time'], utc=True).dt.tz_convert('US/Pacific')
    return vc_df


def load_realtime_data(vid_list=None):
    # Read in GTFS-realtime data
    rt_prefix = '../beb_chargers/data/realtime/metro'
    rt_files = sorted([f for f in os.listdir(rt_prefix) if f[-4:] == '.pkl'])
    df_list = list()
    for f in rt_files:
        fname = rt_prefix + '/' + f
        # Read in realtime data provided by Zack
        df = pd.read_pickle(fname).reset_index(drop=True)
        df = df.astype(
            dtype={
                'vehicle_id': str,
                'scheduleDeviation': int,
                'trip_id': str
            }
        )
        # Convert time column to datetime and change time zone
        df['locationtime'] = pd.to_datetime(
            df['locationtime'].astype(int), unit='s', utc=True).dt.tz_convert('US/Pacific')

        # Filter down realtime data to only include buses in ChargePoint data
        if vid_list is not None:
            df = df[df['vehicle_id'].isin(vid_list)]
        df = df.drop(columns=['orientation'])
        df_list.append(df)
    rt_df = pd.concat(df_list).reset_index()
    # Add a date column for grouping data by day
    rt_df['date'] = pd.to_datetime(rt_df['locationtime'].dt.date)

    return rt_df


def load_stop_times():
    stop_times_df = pd.read_csv(
        '../beb_chargers/data/gtfs/metro_mar24/stop_times.txt',
        dtype={'trip_id': str, 'stop_id': str}
    )
    # Convert to timedeltas
    stop_times_df['departure_timedelta'] = pd.to_timedelta(
        stop_times_df['departure_time'])
    return stop_times_df


def load_trips_file():
    return pd.read_csv(
        '../beb_chargers/data/gtfs/metro_mar24/trips.txt',
        dtype={'trip_id': str, 'shape_id': str, 'route_id': str}
    )


def load_routes_file():
    return pd.read_csv(
        '../beb_chargers/data/gtfs/metro_mar24/routes.txt',
        dtype={'route_id': str, 'route_short_name': str}
    )


def add_gtfs_to_realtime(rt_df):
    # Read in GTFS stop times
    stop_times_df = load_stop_times()
    # Filter down to included trip IDs
    stop_times_df = stop_times_df[
        stop_times_df['trip_id'].isin(rt_df['trip_id'].unique())
    ]

    # Trips file (gives us shape and route IDs)
    trips_df = load_trips_file()
    trips_df = trips_df[trips_df['trip_id'].isin(rt_df['trip_id'].unique())]

    # Routes file (gives us route names)
    routes_df = load_routes_file()

    # Add stop info to realtime
    rt_df = rt_df.merge(
        stop_times_df.drop(
            columns=[
                'arrival_time', 'departure_time', 'stop_headsign', 'pickup_type',
                'drop_off_type', 'shape_dist_traveled', 'timepoint'
            ]
        ),
        left_on=['trip_id', 'nextStop'], right_on=['trip_id', 'stop_id']
    )
    # Add route info to realtime
    rt_df = rt_df.merge(
        trips_df[['trip_id', 'route_id']],
        on='trip_id'
    ).merge(
        routes_df[['route_id', 'route_short_name']],
        on='route_id'
    ).drop(columns=['route_id'])

    # DST causes problems. Add an hour if any times on 3/10/24 are between
    # 02:00:00 and 03:00:00
    departure_srs = rt_df['date'] + rt_df['departure_timedelta']
    problem_ix = departure_srs.between(
        datetime.datetime(2024, 3, 10, 2),
        datetime.datetime(2024, 3, 10, 3)
    )
    departure_srs.loc[problem_ix] += datetime.timedelta(hours=1)
    rt_df['departure_time'] = departure_srs.dt.tz_localize('US/Pacific')

    return rt_df


def summarize_schedule(stop_times_df):
    # Summarize scheduled times from static GTFS
    scheduled_times = pd.DataFrame()
    scheduled_times['start_time_sched'] = stop_times_df.sort_values(
        by=['trip_id', 'departure_time']).groupby('trip_id')[
    ['trip_id', 'departure_time']].head(1).set_index('trip_id')
    scheduled_times['end_time_sched'] = stop_times_df.sort_values(
        by=['trip_id', 'departure_time']).groupby('trip_id')[
    ['trip_id', 'departure_time']].tail(1).set_index('trip_id')
    scheduled_times['duration_sched'] = (
        pd.to_timedelta(scheduled_times['end_time_sched']) - pd.to_timedelta(scheduled_times['start_time_sched'])
    ).dt.total_seconds()
    return scheduled_times


def add_schedule_to_rt_summary(scheduled_times, rt_trip_summary):
    # Add scheduled duration column
    rt_trip_summary = rt_trip_summary.merge(
        scheduled_times[['start_time_sched', 'end_time_sched', 'duration_sched']],
        left_on='trip_id', right_index=True
    )

    rt_trip_summary['start_time_sched'] = rt_trip_summary['date'] + pd.to_timedelta(rt_trip_summary['start_time_sched'])
    rt_trip_summary['end_time_sched'] = rt_trip_summary['date'] + pd.to_timedelta(rt_trip_summary['end_time_sched'])
    rt_trip_summary['start_time_actual'] = rt_trip_summary['start_time_sched'] + pd.to_timedelta(
        rt_trip_summary['delay_at_start'], unit='s'
    )
    rt_trip_summary['end_time_actual'] = rt_trip_summary['end_time_sched'] + pd.to_timedelta(
        rt_trip_summary['delay_at_end'], unit='s'
    )

    # DST causes problems. Add an hour if any times on 3/10/24 are between
    # 02:00:00 and 03:00:00
    start_time_srs = rt_trip_summary['start_time_actual']
    problem_ix = start_time_srs.between(
        datetime.datetime(2024, 3, 10, 2),
        datetime.datetime(2024, 3, 10, 3)
    )
    start_time_srs.loc[problem_ix] += datetime.timedelta(hours=1)
    rt_trip_summary['start_time_actual'] = start_time_srs.dt.tz_localize('US/Pacific')

    end_time_srs = rt_trip_summary['end_time_actual']
    problem_ix = end_time_srs.between(
        datetime.datetime(2024, 3, 10, 2),
        datetime.datetime(2024, 3, 10, 3)
    )
    end_time_srs.loc[problem_ix] += datetime.timedelta(hours=1)
    rt_trip_summary['end_time_actual'] = end_time_srs.dt.tz_localize('US/Pacific')

    rt_trip_summary['time_difference'] = rt_trip_summary['delay_at_end'] - rt_trip_summary['delay_at_start']
    rt_trip_summary['duration_rt'] = rt_trip_summary['time_difference'] + rt_trip_summary['duration_sched']
    rt_trip_summary['time_difference_pct'] = 100 * rt_trip_summary['time_difference'] / rt_trip_summary['duration_sched']

    return rt_trip_summary


def aggregate_energy_data(rt_trip_summary, vc_df):
    # Aggregate ChargePoint data to trip level
    # TODO: confusing code here, using both trip_times_df and rt_trip_summary
    trip_times_df = rt_trip_summary.set_index(['date', 'vehicle_id', 'trip_id'])
    vids = list()
    tids = list()
    kwhs = list()
    mis = list()
    cons = list()
    dates = list()
    n_samples = list()
    for (date, vid, tid) in trip_times_df.index:
        vid_times = rt_trip_summary[
            (rt_trip_summary['vehicle_id'] == vid) & (rt_trip_summary['date'] == date)
        ].set_index('trip_id')
        vid_vc = vc_df[vc_df['Name'] == vid]

        tid_df = vid_vc[vid_vc['ISO Time'].between(
            vid_times.loc[tid, 'start_time_actual'],
            vid_times.loc[tid, 'end_time_actual'],
            inclusive='both'
        )]
        try:
            # Filter out NAs
            tid_full = tid_df[['ISO Time', 'Energy used (kWh)', 'Distance driven (mi)']].dropna().sort_values('ISO Time')
            kwh_0 = tid_full.iloc[0]['Energy used (kWh)']
            dist_0 = tid_full.iloc[0]['Distance driven (mi)']
            kwh_end = tid_full.iloc[-1]['Energy used (kWh)']
            dist_end = tid_full.iloc[-1]['Distance driven (mi)']
            kwh_used = kwh_end - kwh_0
            mi_driven = dist_end - dist_0
            dates.append(date)
            vids.append(vid)
            tids.append(tid)
            kwhs.append(kwh_used)
            mis.append(mi_driven)
            cons.append(kwh_used / mi_driven)
            n_samples.append(len(tid_df))
        except IndexError:
            # We get here if every row has an NA value for either
            # distance or kWh
            pass

    vc_by_trip = pd.DataFrame(
        data={
            'date': dates,
            'vehicle_id': vids,
            'trip_id': tids,
            'kwh': kwhs,
            'miles': mis,
            'kwh_per_mi': cons,
            'n_samples': n_samples
        }
    )

    return vc_by_trip


def build_complete_df(rt_trip_summary, vc_by_trip, trips_df, routes_df):
    # Combine realtime and energy data
    print(f'Energy consumption DF includes {len(vc_by_trip)} trips.')
    cleaned_trip_data = rt_trip_summary[
        ['date', 'vehicle_id', 'trip_id', 'duration_sched', 'duration_rt',
         'time_difference_pct'
        ]
    ].merge(
        vc_by_trip[
            ['date', 'vehicle_id', 'trip_id', 'kwh', 'miles', 'kwh_per_mi']
        ],
        on=['date', 'vehicle_id', 'trip_id']
    )
    print(f'Cleaned trip data includes {len(cleaned_trip_data)} trips after'
          ' initial merge with energy data.')

    # Throw out the trips with questionable data
    cleaned_trip_data = cleaned_trip_data[
        cleaned_trip_data['time_difference_pct'] < 0.4*cleaned_trip_data['time_difference_pct'].max()]
    cleaned_trip_data['vehicle_type'] = cleaned_trip_data['vehicle_id'].str[:2].map({'47': '40-foot', '48': '60-foot'})

    # Clean up and save the data for further analysis
    # Add route info and timing info
    data_out = cleaned_trip_data.merge(
        trips_df[['trip_id', 'route_id', 'direction_id']], on='trip_id').merge(
        routes_df[['route_id', 'route_short_name']]).drop(
        columns=['route_id']).merge(
            rt_trip_summary[['date', 'vehicle_id', 'trip_id', 'start_time_actual', 'end_time_actual']], on=['date', 'vehicle_id', 'trip_id']
    ).rename(
            columns={
                'time_difference_pct': 'duration_difference_pct',
                'route_short_name': 'route',
                'start_time_actual': 'start_time',
                'end_time_actual': 'end_time'
            }
    )
    # Reorder columns
    data_out = data_out[
        ['date', 'vehicle_id', 'vehicle_type', 'trip_id', 'route', 'direction_id', 'start_time', 'end_time',
         'duration_sched', 'duration_rt', 'duration_difference_pct', 'kwh', 'miles', 'kwh_per_mi']
    ]
    return data_out


def run_all_data_processing(bebs_only=False, routes_incl=None):
    # Move working directory up one level (code was originally written
    # in /jupyter directory)
    os.chdir('..')

    vc_df = load_chargepoint_data()

    if bebs_only:
        # Identify all vehicle IDs observed
        vids = vc_df['Name'].unique()
    else:
        vids = None

    rt_df = load_realtime_data(vid_list=vids)

    rt_df = add_gtfs_to_realtime(rt_df)

    # Filter down to routes we plan to analyze
    if routes_incl is not None:
        rt_df = rt_df[rt_df['route_short_name'].isin(routes_incl)]
    print(
        'Realtime dataset contains {} trips to clean'.format(
            len(rt_df[['date', 'trip_id']].drop_duplicates())
        )
    )

    # Summarize realtime data by trip
    rt_trip_summary = summarize_realtime_trips(rt_df)
    write_fname = '../beb_chargers/data/processed/realtime_trips_summary.csv'
    rt_trip_summary.to_csv(write_fname, index=False)

    stop_times_df = load_stop_times()
    scheduled_times = summarize_schedule(stop_times_df)
    # Bring in the static schedule data
    rt_trip_summary = add_schedule_to_rt_summary(
        scheduled_times, rt_trip_summary
    )

    energy_by_trip = aggregate_energy_data(rt_trip_summary, vc_df)
    energy_by_trip.to_csv(
        '../beb_chargers/data/processed/energy_by_trip.csv', index=False
    )

    trips_df = load_trips_file()
    routes_df = load_routes_file()
    data_out = build_complete_df(
        rt_trip_summary, energy_by_trip, trips_df, routes_df
    )
    data_out.to_csv(
        '../beb_chargers/data/processed/full_cleaned_trip_data.csv',
        index=False
    )


if __name__ == '__main__':
    routes = [
        'F Line', 'H Line', '131', '132', '150', '153', '161', '165'
    ]
    run_all_data_processing(bebs_only=False, routes_incl=None)

