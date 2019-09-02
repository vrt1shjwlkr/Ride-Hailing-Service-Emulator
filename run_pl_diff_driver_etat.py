from __future__ import division
import sys, os, logging, itertools, math, threading, random, numpy, csv, time
from subprocess import Popen
from pathlib import Path
from geopy.distance import vincenty
from lppm import *
from globalvars import *
import matplotlib
import matplotlib.pyplot as plt


# Geo-coordinates of the area of interest
lat1 = (48.810519)
lat2 = (48.901606)
lon1 = (2.275873)
lon2 = (2.421079)

db_name = 'cabService_diff_etat'
obf_class_size = 200 # unused


number_riders = 200 # Number of riders in the system
number_drivers = 120 # Number of drivers in the system

configs=[['hard', 'hard', 'hard']] # Drivers' acceptance model, M_d; choose from {[['hard', 'hard', 'hard'], ['hard', 'hard', 'exp'], ['hard', 'hard', 'log'],['log', 'hard', 'exp'], ['hard', 'exp', 'exp'], ['exp', 'exp', 'exp'], ['log','exp','exp'], ['log', 'log', 'hard'], ['log','log','exp'], ['log', 'log', 'log']]}

mechanisms = ['planar_lap'] # Location privacy preserving mechanism to use on the riders' true locations; choose from {'planar_lap','planar_geo','exp'}. Comparison of different LPPMs is shown in Figures 5 and 11. 

run_time = 200 # Running time of a single run of RHS emulation. With more time, more data will be collected
eta_tolerance = 400 # ETA tolerance of drivers; Figure 3 (middle) shows the effect on tailored QL of riders
max_eta_tolerance=2000 # Maximum ETA_t of drivers; more this value, more the data collected
req_delay = 10 # Delay between two successive requests made by a rider
privacy_levels = [1.4] # Privacy level, l, is a parameter of planar laplace and planar geometric mechanisms
genric_utilities = [0.5, 1.0] # Radius, in Km, in which privacy protection is expected, theoretically
obfuscation_level = None # unused
debug_='MEDIUM' # With 'HIGH', detailed execution will be presented. One can manually add prints as well


z_qlg=-1 # unused
g_res=200 # resolution of the grid used for LPPMs for discrete domains such as planar geometric and exponential mechanisms
geo_lat=g_res/(vincenty([0,0], [0,1]).meters)
geo_lon=g_res/(vincenty([0,0], [1,0]).meters)
alpha=calculate_pg_normalizer(privacy_levels[0],genric_utilities[0],g_res) # Normalizer required planar geometric and exponential mechanisms



uniform=1 # If uniform==0, nonuniform rider and driver distributions in the area of interest will be maintained 
uniform_eta=1 # unused
uniform_dm=1 # unused

count=0

while count<5:
	for j in range(0, len(configs)):
		configuration = configs[j]
		dd_surge_neg = configuration[0]
		dd_surge_less_than_one = configuration[1]
		dd_surge_more_than_one = configuration[2]

		while eta_tolerance < max_eta_tolerance+1:
			for mech_number, mech_name in enumerate(mechanisms):
				for i in range(0, len(genric_utilities)):
					exp_folder='./planar_lap_diff_etat_r_%.1f'%genric_utilities[i] # name of the folder in which to save the csv files containing attributes of a ride; check csvGenerator.py for more details
					if not os.path.exists(exp_folder):
					    os.makedirs(exp_folder)

					mongo_cmd = 'python mongodbGenerator.py {} {} 15 {} {} {} {} {} {} {} {} {} {}'.format(number_riders, number_drivers, db_name, mech_name, genric_utilities[i], privacy_levels[0],z_qlg,g_res,uniform,alpha,geo_lat,geo_lon)
					return_value=os.system(mongo_cmd)
					# print('Return value for mongodb call',return_value)

					cmd = 'python cabService.py {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(db_name, obf_class_size, number_riders, number_drivers, genric_utilities[i], 
						obfuscation_level, run_time, eta_tolerance, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, req_delay, mech_name, privacy_levels[0], None, None, None, debug_,count,exp_folder,z_qlg,g_res,uniform_eta,uniform_dm,alpha,geo_lat,geo_lon,uniform)

					print('#############################  Executing next command {} #############################'.format(cmd))
					return_value_=os.system(cmd)
					print('Return value for main call',return_value_)


			eta_tolerance += 200
		eta_tolerance = 400
	count+=1

def extract_datapoint(filename):
	avg_gen=[]
	std_gen=[]
	avg_tai=[]
	std_tai=[]

	tail_ql=[]
	gen_ql=[]
	with open(filename) as f:
		f_reader = csv.reader(f)
		for row in f_reader:
			try:
				avg_gen.append(float(row[17])*10000)
				std_gen.append(float(row[18])*10000)
				avg_tai.append(float(row[19])*100000)
				std_tai.append(float(row[20])*100000)
				tail_ql.append(float(row[9]))
				gen_ql.append(float(row[15]))
			except:
				pass

	return avg_gen,std_gen,avg_tai,std_tai,tail_ql,gen_ql


exp_folder='./planar_lap_diff_etat_r_1.0'
genric_utilities = [1.0]

tail_ql_data=[]
gen_ql_data=[]

tail_ql_data_means=[]
gen_ql_data_means=[]
tail_ql_data_meds=[]
gen_ql_data_meds=[]

for config in configs:

	x=[]
	while eta_tolerance < 2001:
		for mech_number, mech_name in enumerate(mechanisms):
			for i in range(0, len(genric_utilities)):
				foldername = exp_folder+'/results_'+str(eta_tolerance)+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(number_riders)+'_'+str(number_drivers)+'_'+str(genric_utilities[i])
				filename = foldername+'/consolidated_'+mech_name+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(eta_tolerance)+'_'+str(req_delay)+'_'+str(genric_utilities[i])+'.csv'
				consolidated_file = Path('./' +filename)

				avg_gen,std_gen,avg_tai,std_tai,tail_ql,gen_ql=extract_datapoint(filename)
				
				tail_ql_data.append(tail_ql)
				gen_ql_data.append(gen_ql)
				tail_ql_data_means.append(np.mean(np.array(gen_ql)))
				gen_ql_data_means.append(np.mean(np.array(tail_ql)))
				tail_ql_data_meds.append(np.median(np.array(gen_ql)))
				gen_ql_data_meds.append(np.median(np.array(tail_ql)))

				print(genric_utilities[i],np.mean(np.array(gen_ql)),np.mean(np.array(tail_ql)),np.median(np.array(gen_ql)),np.median(np.array(tail_ql)))

				x.append(eta_tolerance)
		eta_tolerance += 200
	eta_tolerance=400



exp_folder='./planar_lap_diff_etat_r_0.5'
genric_utilities = [0.5]

tail_ql_data_9=[]
gen_ql_data_9=[]

tail_ql_data_means_9=[]
gen_ql_data_means_9=[]
tail_ql_data_meds_9=[]
gen_ql_data_meds_9=[]

for config in configs:
	while eta_tolerance < 2001:
		for mech_number, mech_name in enumerate(mechanisms):
			for i in range(0, len(genric_utilities)):
				foldername = exp_folder+'/results_'+str(eta_tolerance)+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(number_riders)+'_'+str(number_drivers)+'_'+str(genric_utilities[i])
				filename = foldername+'/consolidated_'+mech_name+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(eta_tolerance)+'_'+str(req_delay)+'_'+str(genric_utilities[i])+'.csv'
				consolidated_file = Path('./' +filename)

				avg_gen,std_gen,avg_tai,std_tai,tail_ql,gen_ql=extract_datapoint(filename)

				tail_ql_data_9.append(tail_ql)
				gen_ql_data_9.append(gen_ql)

				tail_ql_data_means_9.append(np.mean(np.array(gen_ql)))
				gen_ql_data_means_9.append(np.mean(np.array(tail_ql)))

				tail_ql_data_meds_9.append(np.median(np.array(gen_ql)))
				gen_ql_data_meds_9.append(np.median(np.array(tail_ql)))

				print(genric_utilities[i],np.mean(np.array(gen_ql)),np.mean(np.array(tail_ql)),np.median(np.array(gen_ql)),np.median(np.array(tail_ql)))

		eta_tolerance += 200
	eta_tolerance=400

kwargs = dict(capsize=5, elinewidth=0.6, linewidth=1.1, ms=7)

fig=plt.figure(figsize=(10,8))
ax=fig.add_subplot(111)


bp1_pos=list(np.arange(len(x))-0.09)
bp2_pos=list(np.arange(len(x))-0.03)
bp3_pos=list(np.arange(len(x))+0.03)
bp4_pos=list(np.arange(len(x))+0.09)

bp1=ax.boxplot(gen_ql_data,positions=bp1_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=True,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:crimson'),
	whiskerprops=dict(color='xkcd:crimson'),
	flierprops=dict(color='xkcd:crimson',markeredgecolor='xkcd:crimson'))

bp2=ax.boxplot(tail_ql_data,positions=bp2_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=False,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:blue'),
	whiskerprops=dict(color='xkcd:blue'),
	flierprops=dict(color='xkcd:blue',markeredgecolor='xkcd:blue'))


bp3=ax.boxplot(gen_ql_data_9,positions=bp3_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=True,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:crimson'),
	whiskerprops=dict(color='xkcd:crimson'),
	flierprops=dict(color='xkcd:crimson',markeredgecolor='xkcd:crimson'))

bp4=ax.boxplot(tail_ql_data_9,positions=bp4_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=False,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:blue'),
	whiskerprops=dict(color='xkcd:blue'),
	flierprops=dict(color='xkcd:blue',markeredgecolor='xkcd:blue'))


for bplot in [bp1,bp3]:
    for patch in bplot['boxes']:
        patch.set_facecolor('xkcd:crimson')

x=np.arange(len(x))

ax.errorbar(x, tail_ql_data_meds_9, fmt='.', color='r', linewidth=1, linestyle='-', label='$r$=0.5Km')
ax.errorbar(x, gen_ql_data_meds_9, fmt='.', color='r', linewidth=1, linestyle='-')
ax.errorbar(x, gen_ql_data_meds, fmt='.', color='black', linewidth=1, linestyle='-', label='$r$=1Km')
ax.errorbar(x, tail_ql_data_meds, fmt='.', color='black', linewidth=1, linestyle='-')

plt.legend(loc='best', frameon=True, fontsize=20)
plt.xlabel('$\mathsf{ETA_t}$ of drivers per PRide run', labelpad=15,fontsize=20)
plt.ylabel('Tailored QL (seconds), Generic QL (meters)', labelpad=15,fontsize=20)

plt.show()
try:
	fig.savefig('planar_lap_diff_etat_uniform.pdf')
except:
	pass