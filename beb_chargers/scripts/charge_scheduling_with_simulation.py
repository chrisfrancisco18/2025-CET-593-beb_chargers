"""
This file's usage is deprecated. It was a precursor to the analysis now
contained in dissertation_case_study.py. I am keeping it in the repo
because the run_scheduling_and_sim() function as well as its detailed
docstring may still be useful.
"""

from datetime import datetime
import logging
import pandas as pd
import matplotlib.pyplot as plt
from beb_chargers.gtfs_beb import GTFSData
from beb_chargers.opt.heuristic_charge_scheduling import repeat_heuristic
from beb_chargers.opt.simulation import SimulationBatch
from beb_chargers.scripts.script_helpers import build_trips_df, \
    build_scheduling_inputs, build_sim_inputs, \
    add_realtime_durations, predict_kwh_per_mi, load_realtime_summary


def run_scheduling(case_data, locs_df, u_max, n_runs=20, random_mult=0.5):
    chargers = locs_df.index.tolist()
    rho = (locs_df['kw'] / 60).to_dict()
    result_df = repeat_heuristic(
        case_data, chargers, rho, u_max, n_runs, random_mult, return_type='df'
    )
    return result_df


def run_scheduling_and_sim(
        date: datetime, battery_kwh: int | float, rho_kw: int | float,
        n_runs_3s: int = 30, n_sims: int = 30, ignore_dh: bool = False,
        vary_energy: bool = True, energy_method: str = 'exact',
        energy_quantile: float = 0.5,
        vary_duration: bool = True, duration_method: str = 'exact',
        use_rt_durations: bool = True, duration_quantile: bool = 0.5,
        random_seed: int = 1, min_soc: float = 0.15, max_soc: float = 0.95
):
    """
    Optimize charging schedules using the 3S heuristic algorithm, then
    evaluate performance across different scenarios using the simulation
    platform.

    :param date: Date of analysis. Determines which trips are included
        in the optimization and simulation modules. Influences possible
        simulation parameters including weather conditions and peak/
        off-peak status of trips.
    :param battery_kwh: Total battery capacity in kWh. Will be scaled
        to usable capacity in optimization methods based on min_soc
        and max_soc.
    :param rho_kw: Power output of all chargers in kW.
    :param n_runs_3s: Number of runs of 3S heuristic.
    :param n_sims: Number of simulation runs.
    :param ignore_dh: True if all deadhead distances and times should
        be set to zero in the simulation. This is useful for validating
        consistency with the charge scheduling code, which ignores
        deadhead. Note that there are likely to be errors with unplanned
        charge scheduling in the simulation code if ignore_dh=True.
    :param vary_energy: True if simulation code should randomly set
        energy consumption per trip based on our regression model from
        predict_kwh_per_mi(). False if the average value should always
        be used for each trip.
    :param energy_method: Method used to set optimization parameter
        values for kWh per mile per trip. Can be one of the following:
        - 'exact': use the exact value set for each trip, as if it is
            known precisely in advance
        - 'mean': use the mean value predicted for each trip
        - 'quantile': sample a specified quantile value from the
            trip's estimated distribution. requires setting the
            energy_quantile value.
        - 'constant': use a constant value
    :param energy_quantile: Sample quantile used for setting energy
        consumption parameters in charge scheduling optimization. If
        energy_quantile=0.8, that means we set the energy consumption
        parameters of every trip to their 80th percentile value based
        on the modeled fit from predict_kwh_per_mi(). Ignored if
        energy_method is not 'quantile'.
    :param vary_duration: True if simulation code should randomly set
        duration per trip based on historic data by route. False if the
        scheduled duration should always be used instead.
    :param duration_method: Method used to set optimization parameter
        values for duration of each trip. Can be one of the following:
        - 'exact': use the exact value set for each trip, as if it is
            known precisely in advance
        - 'mean': use the mean value predicted for each trip
        - 'quantile': sample a specified quantile value from the
            trip's estimated distribution. requires setting the
            duration_quantile value.
        - 'scheduled': use the scheduled duration
    :param duration_quantile: Sample quantile used for setting trip
        duration parameters in charge scheduling optimization. If
        duration_quantile=0.8, that means we set the trip duration
        parameter tau of every trip to its 80th percentile value based
        on historic data. Ignored if duration_method is not 'quantile'.
    :param use_rt_durations: True if exact realtime trip durations
        should be used when available. That is, we will check the
        processed data for the estimated actual duration, duration_rt.
        If it's available, it will be used to set the trip durations
        in the simulation process. If not, we will set the trip
        durations randomly based on historic data.
    :param random_seed: NumPy random seed used to generate simulation
        parameters.
    :param min_soc: Minimum battery state of charge, 0 < min_soc < 1.
    :param max_soc: Maximum battery state of charge, 0 < max_soc <= 1.
    """
    # Check inputs are valid
    if (date.year, date.month) not in ((2024, 3), (2024, 4)):
        raise ValueError('Date must be in March or April 2024.')

    if battery_kwh <= 0:
        raise ValueError('Battery size battery_kwh must be positive.')

    if rho_kw <= 0:
        raise ValueError('Charger power rho in kW must be positive.')

    for n in ['n_runs_3s', 'n_sims']:
        if eval(n) < 0:
            raise ValueError(f'{n} must be positive.')

    if min_soc <= 0 or min_soc >= 1.0:
        raise ValueError('min_soc must be between 0 and 1, exclusive.')

    if max_soc <= 0 or max_soc > 1.0:
        raise ValueError(
            'max_soc must be greater than 0 and no greater than 1.'
        )

    if energy_method not in ['exact', 'mean', 'quantile', 'constant']:
        raise ValueError('Invalid energy_method choice')

    if duration_method not in ['exact', 'mean', 'quantile', 'scheduled']:
        raise ValueError('Invalid duration_method choice')

    if energy_method == 'quantile':
        if energy_quantile is None:
            raise ValueError(
                'energy_quantile must be specified when energy_method '
                '== "quantile"'
            )

        if energy_quantile < 0 or energy_quantile > 1:
            raise ValueError(
                'energy_quantile must be between 0 and 1.'
            )

    if duration_method == 'quantile':
        if duration_quantile is None:
            raise ValueError(
                'duration_quantile must be specified when duration_method '
                '== "quantile"'
            )

        if duration_quantile < 0 or duration_quantile > 1:
            raise ValueError(
                'duration_quantile must be between 0 and 1.'
            )

    depot_coords = (47.495809, -122.286190)
    # Usable battery capacity for optimization
    u_max = (max_soc - min_soc) * battery_kwh
    # Date for analysis
    test_date = date

    # Read in charger locations
    chargers_file = '../data/tre_sites.csv'
    locs_df = pd.read_csv(chargers_file, index_col=0)
    locs_df['kw'] = rho_kw
    locs_df['n_chargers'] = 1
    locs_df.rename(columns={'y': 'lat', 'x': 'lon'}, inplace=True)

    # Build dataframe of relevant trips based on GTFS data
    beb_routes = [
        101, 102, 105, 106, 107, 131, 132, 150, 153, 156, 160, 161, 165, 168,
        177, 182, 183, 187, 193, 240
    ]
    # Treat them all as 60-foot bus routes
    routes_60 = beb_routes

    gtfs_dir = '../data/gtfs/metro_mar24'
    gtfs = GTFSData.from_dir(gtfs_dir)
    beb_routes = [str(r) for r in beb_routes]
    beb_trips = build_trips_df(
        gtfs=gtfs,
        date=test_date,
        routes=beb_routes,
        depot_coords=depot_coords,
        add_depot_dh=True,
        add_trip_dh=True,
        routes_60=routes_60
    )

    # Load realtime data
    # Add trip durations
    if vary_duration:
        if use_rt_durations:
            beb_trips = add_realtime_durations(
                trips_to_lookup=beb_trips,
                realtime_summary=load_realtime_summary(),
                sim_all=False
            )
            dur_cts = beb_trips['duration_src'].value_counts()
            print(
                'Obtained observed duration values for {} trips and simulated '
                'duration for {} trips'.format(
                    dur_cts['realtime'], dur_cts['simulated']
                )
            )

        else:
            beb_trips = add_realtime_durations(
                trips_to_lookup=beb_trips,
                realtime_summary=load_realtime_summary(),
                sim_all=True
            )

    else:
        # If we don't vary duration, just set it to what's scheduled
        beb_trips['duration'] = beb_trips['duration_sched']

    beb_trips = predict_kwh_per_mi(beb_trips)

    # Create inputs for charge scheduling algorithm
    case_data = build_scheduling_inputs(
        beb_trips=beb_trips, chargers_df=locs_df, u_max=u_max,
        energy_method=energy_method, duration_method=duration_method,
        energy_quantile=energy_quantile, duration_quantile=duration_quantile
    )

    # Run the scheduling algorithm
    # TODO: should u_max really be a necessary input? At least put it in
    #   case_data
    opt_result = run_scheduling(
        case_data, locs_df, u_max=u_max, random_mult=0.5, n_runs=n_runs_3s
    )

    # Process inputs for simulation
    sim_inputs = build_sim_inputs(
        opt_df=opt_result, beb_trips=beb_trips, depot_coords=depot_coords,
        min_soc=min_soc, max_soc=max_soc, battery_kwh=battery_kwh
    )

    # Run batch simulation
    print('---- batch simulation ----')
    batch = SimulationBatch(
        chargers_df=locs_df, ignore_deadhead=False, n_sims=n_sims,
        vary_energy=vary_energy, vary_duration=vary_duration,
        seed=random_seed, **sim_inputs
    )
    batch.run()
    batch.process_results()
    return batch


def run_quantile_sensitivity(
        battery_kwh, rho_kw, test_date, seed=99, n_sims=30, n_runs_3s=30,
        q_vals=(0.25, 0.5, 0.75), vary='both'
):
    max_soc = 0.95
    min_soc = 0.15

    use_rt_durations = False
    ignore_dh = False

    if vary == 'both':
        vary_duration = True
        vary_energy = True
        energy_method = 'quantile'
        duration_method = 'quantile'
    elif vary == 'energy':
        vary_energy = True
        vary_duration = False
        # use_rt_durations = False
        energy_method = 'quantile'
        duration_method = 'exact'
    elif vary == 'duration':
        vary_energy = False
        ignore_dh = True
        vary_duration = True
        energy_method = 'exact'
        duration_method = 'quantile'
    else:
        raise ValueError(
            'vary must be one of "both", "energy", or "duration"'
        )

    total_delays = dict()
    charging_delays = dict()
    pct_trips_delayed = dict()
    unplanned_chgs = dict()
    dead_batteries = dict()
    missed_trips = dict()
    for q in q_vals:
        print(f'\n ---- running with quantile {q} ----')
        batch_result = run_scheduling_and_sim(
            date=test_date, rho_kw=rho_kw, battery_kwh=battery_kwh,
            use_rt_durations=use_rt_durations, random_seed=seed, n_sims=n_sims,
            n_runs_3s=n_runs_3s, min_soc=min_soc, max_soc=max_soc,
            vary_duration=vary_duration, vary_energy=vary_energy,
            energy_method=energy_method, duration_method=duration_method,
            ignore_dh=ignore_dh, energy_quantile=q, duration_quantile=q
        )
        total_delays[q] = batch_result.delay
        charging_delays[q] = batch_result.charging_delay
        pct_trips_delayed[q] = batch_result.pct_trips_delayed
        unplanned_chgs[q] = batch_result.n_unplanned_charges
        dead_batteries[q] = batch_result.n_dead_batteries
        missed_trips[q] = batch_result.n_missed_trips

    names = [
        'Charging-Induced Delay (minutes)', 'Number of Unplanned Charges',
        'Number of Dead Batteries', 'Number of Missed Trips'
     ]
    for ix, d in enumerate(
            [charging_delays, unplanned_chgs, dead_batteries, missed_trips]
    ):
        # Boxplot of total delay
        fig, ax = plt.subplots()
        ax.set_ylabel(names[ix])
        ax.set_xlabel('Quantile used in optimization')

        ax.boxplot(
            list(d.values()), tick_labels=list(d.keys())
        )
        vary_str = 'Varying ' + {
            'both': 'Energy Consumption and Duration',
            'energy': 'Energy',
            'duration': 'Duration'
        }[vary] + ':'
        plt.title(
            f'{vary_str}\n'
            f'{rho_kw} kW Chargers and {battery_kwh} kWh Batteries')

        plt.show()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_quantile_sensitivity(
        seed=26,
        battery_kwh=525,
        rho_kw=220,
        test_date=datetime(2024, 4, 1),
        n_sims=3,
        n_runs_3s=100,
        vary='duration',
        q_vals=[0.4, 0.5, 0.6]
        # q_vals=[0.4, 0.5, 0.6, 0.75, 0.9, 0.95]  # , 0.99, 0.999]
    )
