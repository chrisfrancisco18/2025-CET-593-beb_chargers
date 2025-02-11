# `beb_chargers` repository
All code in this repository was created and is owned by Dr. Dan McCabe (dmccabe@uw.edu). This repository was created and shared for the 2025 CET 593 battery-electric (BEB) charger exercise and class project

## Repository Structure
* `beb_chargers`
  * Home to all source code including optimization models, data handling, and ZEBRA app.
  * `archived_app`
    * Archived pages from original draft of charger location optimization app. To be integrated with current version of ZEBRA and deleted when no longer useful.
  * `data`
    * Directory hosting all data used by models and apps in the repo, including GTFS data. Includes some empty directories used to store results of e.g. OpenStreetMap API calls to speed up model runs.
  * `gtfs_beb`
    * Package for handling GTFS data and processing it into formats expected by both ZEBRA app and optimization code.
  * `opt`
    * Python modules related to optimization models and related functions.
  * `scripts`
    * Scripts that run source code from the other directories, e.g. for journal paper case studies.
  * `vis`
    * Visualization code
* `jupyter`
  * Houses a few useful jupyter notebooks, mainly for analyzing project results.
* `results`
  * Empty directory used to store results of model runs as they are collected.

## Setup
### Getting Python
You can download and install Python from the website or Anaconda. Please make sure than your version is Python 3.11 or newer. (I use Python 3.12)
### Getting Git
To work on your local computer, you need Git. See https://git-scm.com
After installing Git, make sure you add the Git to the PATH
### Getting Gurobi license
The optimization model implemented in this project uses gurobi. The large optimization model requires the license. But, you can obtain the academic license from https://www.gurobi.com/ for free using UW email. The free academic license is valid for one year. You can obtain new licenses as long as you are eligible.
To get the license:
0. Create the account (with UW email)
1. Login & Click 'Licenses' icon on the left tab
2. Click 'Request' icon
3. Select Named-User Academic and Click 'GENERATE NOW!' icon
4. Click 'Licenses' icon and and Download newly generated license
When you click download icon, it should display instruction for gurobi installation and gurobi license. You need the gurobi sofeware before install the license. Please noted that the version of gurobi license should match you python version.
### Getting API keys
Some configuration is needed prior to running the code in this repository. In particular, some of the code relies on public APIs that require a key for usage. Because these APIs have limited usage allowed before they start incurring costs, users of this repo need to provide their own API keys. These API keys should be stored in a `.env` file in the root directory of the repo (i.e., `beb_chargers/.env`). We use the `python-dotenv` package to read these in as environment variables where needed.

The `.env` file should be formatted as follows with the following entries:

```
# Openrouteservice
ORS_KEY=your_ors_key
# Google Maps Directions API
GMAPS_KEY=your_googlemaps_key
# Mapbox (used via Plotly)
MAPBOX_KEY=your_mapbox_key
```

To obtain these keys, follow the steps for each provider. See https://openrouteservice.org/dev/#/signup for Openrouteservice, https://developers.google.com/maps/documentation/directions/overview for Google Maps Directions, and https://docs.mapbox.com/help/getting-started/access-tokens/ for Mapbox.

# How to run charger location example jupyter notebook???
## Option 1: Simple way (without cloning Git repo) `Charger Location Example without Cloning Git Repo.ipynb` file
This way is for anyone especially those who never experience cloning git repository before.
### Setup
- Store `.env` and `Charger Location Example without Cloning Git Repo.ipynb` file in the same folder.
- You can store your data folder any where you want. Just make sure that you update the path for file location in the Jupyter Notebook
### Install beb_chargers and other required libraries
In the Jupyter Notebook, you need to run these codes to install all libraries you needed for beb_chargers
```
  !pip install git+https://github.com/chrisfrancisco18/2025-CET-593-beb_chargers.git
  !pip install -r https://raw.githubusercontent.com/chrisfrancisco18/2025-CET-593-beb_chargers/main/requirements.txt
```

### where can I get a data:
https://uwnetid-my.sharepoint.com/:u:/g/personal/pritthik_uw_edu/Ee5LQ_KZkAVMrS8ocT8eUHQBeVcvyuZU1WGVEhTf2O9Bpg?e=U8jfrU
(UW Email Required)

## Option 2: Clone Git `Charger Location.ipynb` file
For those who are more familiar with GitHub, you can clone the repository
### Clone the Repository
Open Terminal and run:
```
  git clone https://github.com/chrisfrancisco18/2025-CET-593-beb_chargers.git
  cd 2025-CET-593-beb_chargers
```
### (Optional) Create & Activate a Virtual Environment
It will install dependecies in a virtual environment to avoid conflicts
I use Anaconda, create a Conda environment:
```
  conda create --name beb_env python=3.12
  conda activate beb_env
```
You can replace `beb_env` with anyname you want
### Install Dependencies from `requirements.txt`
```
  pip install -r requirements.txt
```
This ensures all external dependencies are installed before installing the package itself.
### Install the Package Using `setup.py`
```
  pip install .
```
This installs the package itself so you can import and use it.
### Store files
- Store `.env` file in the root directory of the repo (i.e., beb_chargers/.env).
- Store (any) GTFS files in beb_chargers\data\gtfs folder
- Store (any) site location files in beb_chargers\data\site_location