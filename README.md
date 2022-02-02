### Fertility_Functions.py

Classes for fertility (brood size) data manipulation and database entry.
Plotting functions specific to the Fertility screen.

### Flybase_Functions.py

Extraction of IDs, annotations, gene names from FlyBase data.

### Flywheel_AlignFunctions.py

Contains functions for the setup of FlyWheel images; detection of plate edges, wells, image alignment etc.

### Flywheel_TrackFunctions.py

Contains functions to analyse the FlyWheel images to track fly motion.
Plotting functions for the derived tracking data.

### GenomeRNAi_Functions.py

Funtions for storing and retrieving RNAi validation results.

### GraphKnownnessChanges.py

A simple script to graph historical changes in knownness,

### QAFF_Functions.py

Classes for quantitative analysis of fly faeces data manipulation and database entry.
Functions for processing plate images and extracting metrics for analysis.

### ROS_analysis.py

Extra functions for processing redox stress survival in FlyWheel data and related database storage.

### Unknome_Functions.py

Contains the top-level Unknome class for organising and plotting the fly screening data, obtaining IDs etc.
Also contains classes for plotting expression , KK library stats and FlyBase references.

### Viability_Functions.py

Class for database entry of fly viability screening.

### iFly_Functions.py

Classes for iFly motility data manipulation and database entry.
Plotting functions for iFly data.

### iSpots_Functions.py

Fluorescent eye spot database entry and data manipulation.
Includes plotting and visualisation functions.

### iWing_Functions.py

Classes for wing area data manipulation and database entry.
Includes plotting and visualisation functions.


## Scripts for plotting and calling phenotypic screen outliers

The most recent outlier anlysis was done externally, and the data is pulled back into the database.

### Fertility_outliers.py

### QAFF_outliers.py

### Survival_outliers.py

### iFly_outliers.py

### iSpots_outliers.py

### iWing_outliers.py

## Utility files

### RobustStats_Functions.py

Helper functions for performing statistical analyses robust to outliers.

### Plot_Functions.py

A few funtions to help with matplotlib plotting.

### collections.py

Extensions to basic Python collection types. Mostly obsolete.

### sqliteFunctions.py

Verybasic database creation functions.

### statsFunctions.py

Simple statstical functions. Fairly plain python rather than NumPy/SciPy.

### File_Functions.py

General fileI/O helper functions.
