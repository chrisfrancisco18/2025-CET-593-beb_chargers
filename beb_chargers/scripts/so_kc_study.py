import logging
from beb_chargers.scripts.king_county_study import run_facility_location
from beb_chargers.opt.evaluation import SimulationRun

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # logging.getLogger("beb_model").setLevel(logging.DEBUG)

    # Define inputs
    depot_coords = (47.495809, -122.286190)
    # CSV file giving candidate charger sites
    site_fname = 'data/so_king_cty_sites.csv'

    # 40-ft routes from interim base
    # Source: Metro BEB Implementation report, 2020
    interim_40 = [22, 116, 153, 154, 156, 157, 158, 159, 168, 169, 177, 179,
                  180, 181, 182, 183, 186, 187, 190, 192, 193, 197]
    # 60-ft routes from interim base
    interim_60 = [101, 102, 111, 116, 143, 150, 157, 158, 159, 177, 178, 179,
                  180, 190, 192, 193, 197]
    interim_rts = list(set(interim_40 + interim_60))

    # Battery capacity in kWh
    battery_cap = 466 * 0.75
    # Energy consumption rate in kWh per mile
    kwh_per_mile = 3
    # Power output of each charger
    chg_pwrs = 300/60
    # Charger construction cost
    s_cost = 200000
    c_cost = 698447
    n_max = 4
    # Metro operating expenses:
    # https://www.transit.dot.gov/ntd/data-product/2020-annual-database-operating-expenses
    # Metro total hours worked:
    # https://www.transit.dot.gov/ntd/data-product/2019-annual-database-transit-agency-employees
    alpha = 190*365*12/60

    flm = run_facility_location(
        route_list=interim_60, site_file=site_fname, battery_cap=battery_cap,
        kwh_per_mile=kwh_per_mile, charge_power=chg_pwrs, site_cost=s_cost,
        charger_cost=c_cost, alpha=alpha, max_chargers=n_max, opt_gap=None,
        depot_coords=depot_coords, pickle_fname='so_kc_inputs.pickle',
        save_fname='../results/so_kc_results.csv',
        summary_fname='../results/so_kc_summary.csv')

    # flm.plot_chg_ratios()

    # Extract needed outputs
    sim = SimulationRun(
        om=flm, chg_plan=flm.chg_schedule, site_caps=flm.num_chargers)
    print('\nEVALUATION RESULTS')
    sim.run_sim()
    sim.process_results()
    sim.print_results()

    # Batch simulation
    # batch = SimulationBatch(om=flm, sched=flm.chg_schedule, n_sims=100,
    #                         site_caps=flm.num_chargers, energy_std=0.01,
    #                         seed=17)
    # batch.run()
    # print('\nSIMULATION RESULTS')
    # batch.process_results()