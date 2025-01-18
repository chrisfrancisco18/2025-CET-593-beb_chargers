import logging
import datetime
from king_county_study import run_facility_location


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # logging.getLogger("beb_model").setLevel(logging.DEBUG)

    # Define inputs
    depot_coords = (47.495809, -122.286190)
    # CSV file giving candidate charger sites
    # site_fname = '../data/tre_sites.csv'
    site_fname = '../data/so_king_cty_sites.csv'

    # Tried adding 148 as well, but most of its blocks are infeasible
    # b/c they have no layover time in Renton. 181 also tends to create
    # infeasible blocks.
    beb_routes = [
        101, 102, 105, 106, 107, 131, 132, 150, 153, 156, 160, 161, 165, 168,
        177, 182, 183, 187, 193, 240
    ]
    beb_routes = [str(r) for r in beb_routes]

    # Battery capacity in kWh
    battery_cap = 525 * 0.8
    # Energy consumption rate in kWh per mile
    kwh_per_mile = 3
    # Power output of each charger
    chg_pwrs = 220 / 60
    # Charger construction cost
    s_cost = 200000
    c_cost = 698447

    n_max = 4
    alpha = 190 * 365 * 12 / 60

    flm = run_facility_location(
        route_list=beb_routes, site_file=site_fname, battery_cap=battery_cap,
        kwh_per_mile=kwh_per_mile, charge_power=chg_pwrs, site_cost=s_cost,
        charger_cost=c_cost, alpha=alpha, max_chargers=n_max, opt_gap=0.01,
        depot_coords=depot_coords, pickle_fname='../data/metro_inputs.pickle',
        save_fname='../../results/metro_case_results.csv',
        summary_fname='../../results/metro_case_summary.csv',
        gtfs_dir='../data/gtfs/metro_mar24',
        test_date=datetime.datetime(2024, 3, 28))

    # Build up simulation instance

    # Extract needed outputs
    # TODO: sometimes seeing an unscheduled charge where it isn't
    #   expected
    # sim = SimulationRun.from_ocl_model(
    #     om=flm, chg_plan=flm.chg_schedule, site_caps=flm.num_chargers)
    # print('\nEVALUATION RESULTS')
    # sim.run_sim()
    # sim.process_results()
    # sim.print_results()

    # flm.plot_chg_ratios()


