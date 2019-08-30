# Ride-Hailing-Service-Emulator






commands:
To create mongodb database use:
	python mongodbGenerator.py <num_of_riders> <num_of_drivers> <num_of_regions> <database_name> <lppm_name> <generic_utility> <privacy_level>
	sample - python mongodbGenerator.py 100 40 30 cabService
	
To run ride hailing service simulation use:
	python cabService.py <db_name> <obfuscation_class_size> <num_of_riders> <num_of_drivers> <obfuscation_level> <gen_utility> <simulation_time> <eta_tolerance> <eta_diff_tolerance>
	sample - python cabService.py cabService 200 100 60 0.1 1 10 450 150