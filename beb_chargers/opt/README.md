# opt
This directory contains optimization code for the `beb_chargers` project. The modules are organized as follows:

- `benders.py`
  - This module contains functions that implement Combinatorial Benders decomposition, used to solve the charging scheduling problem.
- `evaluation.py`
  - This module contains simulation and evaluation code, most importantly a discrete event simulation model, to test the performance of the optimization models across various scenarios.
- `heuristics.py`
  - Heuristic algorithms for solving the charging scheduling problem, including our 3S heuristic.
- `model.py`
  - The BEB Optimal Charger Location (BEB-OCL) model implementation, via the `ChargerLocationModel` class.
- `opt_utils.py`
  - Utility functions that may be used by various optimization models. As of writing, this is just the `LagrangeModel` class used to implement Lagrangian Relaxation.