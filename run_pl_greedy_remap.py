import sys, os, logging, itertools, math, threading, random, csv,time
import numpy as np
from globalvars import *
from subprocess import Popen
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
from lppm_planar_geo import *
from geopy.distance import vincenty

#Paris
lat1 = (48.810519)
lat2 = (48.901606)
lon1 = (2.275873)
lon2 = (2.421079)

db_name = 'cabService_pl_greedy_remap'
obf_class_size = 200
number_riders = 200
number_drivers = 120

configs=[['hard', 'hard', 'hard']]

run_time = 400
eta_tolerance = 400
req_delay = 10
privacy_levels = [1.4]
genric_utilities = [0.2,0.4,0.6,0.8,1.0,1.2,1.4]

obfuscation_level = None
debug_='MEDIUM'
z_qlg=-1
g_res=100
geo_lat=g_res/(vincenty([0,0], [0,1]).meters)
geo_lon=g_res/(vincenty([0,0], [1,0]).meters)
alpha=calculate_pg_normalizer(privacy_levels[0],genric_utilities[0],g_res)


uniform=0
r_uniform=1
uniform_eta=1
uniform_dm=1
g_remap=0

print('=====> Generate results using planar laplace mechanism with greedy remap set to %d'%g_remap)

mechanisms = ['planar_lap']

exp_folder='./planar_lap_no_remap'

if not os.path.exists(exp_folder):
    os.makedirs(exp_folder)


count=0

while count<5:
	for j in range(0, len(configs)):
		configuration = configs[j]
		dd_surge_neg = configuration[0]
		dd_surge_less_than_one = configuration[1]
		dd_surge_more_than_one = configuration[2]

		while eta_tolerance < 401:
			for mech_number, mech_name in enumerate(mechanisms):
				for i in range(0, len(genric_utilities)):

					mongo_cmd = 'python mongodbGenerator.py {} {} 15 {} {} {} {} {} {} {} {} {} {} {}'.format(number_riders, number_drivers, db_name, mech_name, genric_utilities[i], privacy_levels[0],z_qlg,g_res,uniform,alpha,geo_lat,geo_lon,r_uniform,g_remap)
					return_value=os.system(mongo_cmd)
					# print('Return value for mongodb call',return_value)

					cmd = 'python cabService.py {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(db_name, obf_class_size, number_riders, number_drivers, genric_utilities[i], 
						obfuscation_level, run_time, eta_tolerance, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, req_delay, mech_name, privacy_levels[0], None, None, None, debug_,count,exp_folder,z_qlg,g_res,uniform_eta,uniform_dm,alpha,geo_lat,geo_lon,uniform,r_uniform,g_remap)

					print('#############################  Executing next command {} #############################'.format(cmd))
					return_value_=os.system(cmd)
					print('Return value for main call',return_value_)

			eta_tolerance += 200
		eta_tolerance = 400
	count+=1



#######################################################################################################################################


g_remap=1

print('=====> Generate results using planar laplace mechanism with greedy remap set to %d'%g_remap)

exp_folder='./planar_lap_greedy_remap'

if not os.path.exists(exp_folder):
    os.makedirs(exp_folder)


count=0
while count<5:
	for j in range(0, len(configs)):
		configuration = configs[j]
		dd_surge_neg = configuration[0]
		dd_surge_less_than_one = configuration[1]
		dd_surge_more_than_one = configuration[2]

		while eta_tolerance < 401:
			data_r_per_mech = []
			data_d_per_mech = []
			for mech_number, mech_name in enumerate(mechanisms):
				for i in range(0, len(genric_utilities)):
					alpha=calculate_pg_normalizer(privacy_levels[0],genric_utilities[i],g_res)
					
					mongo_cmd = 'python mongodbGenerator.py {} {} 15 {} {} {} {} {} {} {} {} {} {} {} {}'.format(number_riders, number_drivers, db_name, mech_name, genric_utilities[i], privacy_levels[0],z_qlg,g_res,uniform,alpha,geo_lat,geo_lon,r_uniform,g_remap)
					return_value=os.system(mongo_cmd)
					# print('Return value for mongodb call',return_value)

					cmd = 'python cabService.py {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(db_name, obf_class_size, number_riders, number_drivers, genric_utilities[i], 
						obfuscation_level, run_time, eta_tolerance, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, req_delay, mech_name, privacy_levels[0], None, None, None, debug_,count,exp_folder,z_qlg,g_res,uniform_eta,uniform_dm,alpha,geo_lat,geo_lon,uniform,r_uniform,g_remap)

					print('#############################  Executing next command {} #############################'.format(cmd))
					return_value_=os.system(cmd)
					print('Return value for main call',return_value_)
					


			eta_tolerance += 200
		eta_tolerance = 400
	count+=1



print('=====> Generating plots for the comparison between planar laplance and planar geometric mechanisms ')


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



tail_ql_data_5=[]
gen_ql_data_5=[]

tail_ql_data_means_5=[]
gen_ql_data_means_5=[]
tail_ql_data_meds_5=[]
gen_ql_data_meds_5=[]

exp_folder='./planar_lap_no_remap'
eta_tolerance=400
x=[]

for config in configs:
	for mech_number, mech_name in enumerate(mechanisms):
		for i in range(0, len(genric_utilities)):
			foldername = exp_folder+'/results_'+str(eta_tolerance)+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(number_riders)+'_'+str(number_drivers)+'_'+str(genric_utilities[i])
			filename = foldername+'/consolidated_'+mech_name+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(eta_tolerance)+'_'+str(req_delay)+'_'+str(genric_utilities[i])+'.csv'
			#filename = foldername+'/consolidated_'+mech_name+'_'+config[0]+'_'+config[1]+'_'+config[2]+'_'+str(eta_tolerance)+'_'+str(req_delay)+'.csv'
			consolidated_file = Path('./' +filename)

			avg_gen,std_gen,avg_tai,std_tai,tail_ql,gen_ql=extract_datapoint(filename)

			tail_ql_data_5.append(tail_ql)
			gen_ql_data_5.append(gen_ql)
			x.append(genric_utilities[i])
			
			tail_ql_data_means_5.append(np.mean(np.array(gen_ql)))
			gen_ql_data_means_5.append(np.mean(np.array(tail_ql)))

			tail_ql_data_meds_5.append(np.median(np.array(gen_ql)))
			gen_ql_data_meds_5.append(np.median(np.array(tail_ql)))

			print(genric_utilities[i],np.mean(np.array(gen_ql)),np.mean(np.array(tail_ql)),np.median(np.array(gen_ql)),np.median(np.array(tail_ql)))


tail_ql_data=[]
gen_ql_data=[]

tail_ql_data_means=[]
gen_ql_data_means=[]
tail_ql_data_meds=[]
gen_ql_data_meds=[]


exp_folder='./planar_lap_greedy_remap'
eta_tolerance=400


for config in configs:
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




# print(x)
kwargs = dict(capsize=2, elinewidth=0.6, linewidth=1.1, linestyle='-', ms=7)

fig=plt.figure(figsize=(10,8))
ax=fig.add_subplot(111)


bp2_pos=list(np.arange(len(x))-0.09)
bp3_pos=list(np.arange(len(x))-0.03)
bp4_pos=list(np.arange(len(x))+0.03)
bp5_pos=list(np.arange(len(x))+0.09)

bp1=ax.boxplot(gen_ql_data,positions=bp1_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=True,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:crimson'),
	whiskerprops=dict(color='xkcd:crimson'),
	flierprops=dict(color='xkcd:crimson',markeredgecolor='xkcd:crimson'))

bp2=ax.boxplot(tail_ql_data,positions=bp2_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=False,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:blue'),
	whiskerprops=dict(color='xkcd:blue'),
	flierprops=dict(color='xkcd:blue',markeredgecolor='xkcd:blue'))

bp5=ax.boxplot(gen_ql_data_5,positions=bp5_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=True,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:crimson'),
	whiskerprops=dict(color='xkcd:crimson'),
	flierprops=dict(color='xkcd:crimson',markeredgecolor='xkcd:crimson'))

bp6=ax.boxplot(tail_ql_data_5,positions=bp6_pos,showmeans=True,meanline=True,widths=[0.1]*len(x),sym='+',patch_artist=False,autorange=True,labels=x,showfliers=False,
	boxprops=dict(color='xkcd:blue'),
	whiskerprops=dict(color='xkcd:blue'),
	flierprops=dict(color='xkcd:blue',markeredgecolor='xkcd:blue'))

for bplot in (bp1, bp5):
    for patch in bplot['boxes']:
        patch.set_facecolor('xkcd:crimson')

x=np.arange(len(x))
# ql_t_max=[750]*(len(x)-1)
# ql_g_max=[2000]*(len(x)-1)
# ax.plot(x[:6],ql_t_max, color='black', linewidth=1, linestyle='--')
# ax.plot(x[:6],ql_g_max, color='black', linewidth=1, linestyle='--')
# plt.axvline(x=2.1, color='b', linewidth=.5, linestyle='--')
# plt.axvline(x=6.1, color='b', linewidth=.5, linestyle='--')
ax.errorbar(x, tail_ql_data_meds, fmt='.', color='r', linewidth=1, linestyle='-', label='with remap')
ax.errorbar(x, gen_ql_data_meds, fmt='.', color='r', linewidth=1, linestyle='--')
ax.errorbar(x, gen_ql_data_meds_5, fmt='.', color='olivedrab', linewidth=1, linestyle='--')
ax.errorbar(x, tail_ql_data_meds_5, fmt='.', color='olivedrab', linewidth=1, linestyle='-', label='without remap')

plt.legend(loc='best', frameon=True, fontsize=20)
plt.xlabel('privacy radius $r$ (Km)', labelpad=15,fontsize=20)
plt.ylabel('Tailored QL (seconds), Generic QL (meters)', labelpad=15,fontsize=20)

try:
	fig.savefig('Fig6_pl_greedy_remap.pdf')
except:
	pass