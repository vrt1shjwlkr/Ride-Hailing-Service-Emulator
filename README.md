# Ride-Hailing-Service-Emulator

Ride hailing service emulator (RHSE) is built to collect the data of commonly occuring scenarios in ride hailing services (RHS) such as Uber and Lyft. RHSE is a simple tool in Python which can be tuned to different scenarios of RHSes. Below, we detail the requirements and setup instructions to use the tool.


## Requirements:

- MongoBooster 3.6
- Python; the tool is tested with Python 3.6. Python packages required are listed in requirements.txt and can be installed using pip install -r requirements.txt

## High level flow of the code:

- RHSE first generates a database of riders and drivers using mongodbGenerator.py. The database is then managed using a mongoDB client, PyMongo. For GUI of the database created, use any GUI client of MongoDB.
- Then riders start sending ride requests and based on availability, drivers accept them. A flow -- ride request to completion -- of a typical scenario in RHSes is given in Figure 1.
- Various attributes of each of the completed rides are logged in a csv file in appropriate folder.

## Configuring scenarios:

- RHSE is built to configure different scenarios of RHSes, as described in Section 5.2. RHSes are complex systems with multiple tunable parameters, including the ones given in Table 4. We have detailed the description and variable name of each in run_pl_diff_driver_eta.py.

## Reproducing the results in the paper:

We give somescripts to run to reproduce the results in the paper. The specific scripts and the corresponding results in the paper are as follows:


commands:
To create mongodb database use:
	python mongodbGenerator.py <num_of_riders> <num_of_drivers> <num_of_regions> <database_name> <lppm_name> <generic_utility> <privacy_level>
	sample - python mongodbGenerator.py 100 40 30 cabService
	
To run ride hailing service simulation use:
	python cabService.py <db_name> <obfuscation_class_size> <num_of_riders> <num_of_drivers> <obfuscation_level> <gen_utility> <simulation_time> <eta_tolerance> <eta_diff_tolerance>
	sample - python cabService.py cabService 200 100 60 0.1 1 10 450 150
