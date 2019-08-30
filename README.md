# Ride-Hailing-Service-Emulator

Ride hailing service emulator (RHSE) is built to collect data of commonly occuring scenarios in ride hailing services (RHS) such as Uber and Lyft. RHSE is a simple tool in Python which can be tuned to different scenarios of RHSes. Below, we detail the requirements and setup instructions to use the tool.




commands:
To create mongodb database use:
	python mongodbGenerator.py <num_of_riders> <num_of_drivers> <num_of_regions> <database_name> <lppm_name> <generic_utility> <privacy_level>
	sample - python mongodbGenerator.py 100 40 30 cabService
	
To run ride hailing service simulation use:
	python cabService.py <db_name> <obfuscation_class_size> <num_of_riders> <num_of_drivers> <obfuscation_level> <gen_utility> <simulation_time> <eta_tolerance> <eta_diff_tolerance>
	sample - python cabService.py cabService 200 100 60 0.1 1 10 450 150
