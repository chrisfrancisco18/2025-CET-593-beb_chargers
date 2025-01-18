# scripts
This directory includes scripts used for various stages of analyses, including processing data and running case studies for optimization models.

- `charge_scheduling_with_simulation.py`: 
- `dissertation_case_study.py`: scripts for running case study instances from the final chapter of my dissertation. This includes both optimization models and using the simulation platform to evaluate performance across various scenarios.
- `kcm_2024_data_processing.py`: this script processes energy consumption and on-time performance data from King County Metro into trip-level summaries used as inputs to the simulation model. These output files are included in the repository and the script is just a reference for how that processing was done, or it can be used to process updated data.
- `king_county_study.py`: This script was originally used for the case study in our *Transportation Research Part C* paper. Some functions it calls were revised during my dissertation work and the script would need to be updated to run the same analysis again.
- `script_helpers.py`: This module contains helper functions used by various scripts that run test cases, to help with reproducibility. These functions help with processing data and providing inputs to optimization methods in the expected format.
- `sensitivity.py`