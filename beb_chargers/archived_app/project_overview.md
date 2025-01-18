# Battery-Electric Bus Layover Charging Optimization
This overview page is a work in progress. Some specific details won't be filled in until the app is nearly complete since the workflow and UI may change as we expand functionality.

## Introduction
This app provides an interface for selecting layover charging sites for battery-electric buses (BEBs). By *layover charging*, we mean high-power charging at established layover sites where buses are idle in between passenger trips, which may sometimes also be called *opportunity charging* or *on-route charging* by other authors.

## Limitations
- Focused on King County, WA
- Support for additional locations is evolving and may be more error-prone
- Limited control over inputs (e.g. buses are homogeneous, only one depot)

## Data Requirements
- List required fields for GTFS
- Mention technology input needs and defaults

## Model Overview
 Our analysis is centered on running the Battery-Electric Bus Block Revision Problem (BEB-BRP) and Battery-Electric Bus Optimal Charger Location (BEB-OCL) models. To learn more about the models used in this work, please see our recent publication here: https://www.sciencedirect.com/science/article/pii/S0968090X23001468?dgcid=coauthor.

 Before deploying the app, we will add more details here (e.g., useful figures from the paper giving a basic idea of the models and how they relate to each other).

## Navigating the App
Use the page index in the sidebar to navigate through the app. For best performance, click through all pages sequentially from top to bottom. There are three stages to running the app: setting the inputs, running the optimization, and examining the results. You can always go back to adjust some inputs, re-optimize, and check the new results.