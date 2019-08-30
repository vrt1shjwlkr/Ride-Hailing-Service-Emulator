from __future__ import division
import simpy, os, datetime, random, simplejson, urllib, csv, sys, collections, math, logging, threading
import numpy as np
from globalvars import *
from pymongo import MongoClient
from driver import Driver
from rider import Rider
from server import Server
from csvGenerator import *
from estimateETA import *
 
def simulation(env, db_name, debug_, obf_class_size, num_riders, num_drivers, gen_utility, obf_level, env_time, eta_tolerance, dd_surge_neg,
    dd_surge_less_than_one, dd_surge_more_than_one, req_delay, mech_name, privacy_level, regression_data_file, d_regression_data_file, 
    mech_number,count,exp_folder,z_qlg, g_res,alpha,geo_lat,geo_lon,uniform_eta=1,uniform_dm=1,uniform=1):
    # Name of file to save data to
    gen_utility_name = 'NA' if gen_utility == None else str(int(1000 * gen_utility))
    privacy_level_name = str(privacy_level)
    obf_level_name = 'NA' if obf_level == None else str(obf_level)

    foldername = exp_folder+'/results_'+str(eta_tolerance)+'_'+dd_surge_neg+'_'+dd_surge_less_than_one+'_'+dd_surge_more_than_one+'_'+str(num_riders)+'_'+str(num_drivers)+'_'+str(gen_utility)

    if not os.path.exists(foldername):
        os.makedirs(foldername)

    filename=foldername+'/rider_results_'+mech_name+'_'+str(obf_class_size)+'_'+str(num_riders)+'_'+str(num_drivers)+'_'+str(env_time)+'_'+ gen_utility_name + '_' + privacy_level_name + '_' + obf_level_name +'_'+str(eta_tolerance)+'_'+str(count)+'.csv'
    filename_d=foldername+'/driver_results_'+mech_name+'_'+str(obf_class_size)+'_'+str(num_riders)+'_'+str(num_drivers)+'_'+str(env_time)+'_'+ gen_utility_name + '_' + privacy_level_name + '_' + obf_level_name +'_'+str(eta_tolerance)+'_'+str(count)+'.csv'

    # Connect to mongodb database
    client = MongoClient()
    mongoClient = MongoClient('mongodb://localhost',27017)

    # Create server, riders, drivers, globals
    database = mongoClient[db_name]
    server = Server(database, debug_,z_qlg)
    riderIDs = list(mongoClient[db_name].riders.distinct("userID"))

    for i in range(num_riders):
        server.riderObjects.append(Rider(i, server, debug_, gen_utility, obf_level, req_delay, mech_name, privacy_level,z_qlg,g_res,alpha,geo_lat,geo_lon))

    for i in range(num_drivers):
        server.driverObjects.append(Driver(i, server, debug_, eta_tolerance, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, gen_utility, mech_name, privacy_level,z_qlg,g_res,uniform_eta,uniform_dm,uniform))

    env.process(server.run(env))

    for i in range(num_riders):
        env.process(server.riderObjects[i].run(env))

    for i in range(num_drivers):
        env.process(server.driverObjects[i].run(env))

    # driver_ops = threading.Thread(target=manage_drivers, args=(server, env))

    # driver_ops.daemon = True
    
    while True:
        if env.now == env_time - 1:
            print('============== Calculating utility loss due to incomplete rides ==============')
            etaEstimate(server, env_time, database,uniform_eta)
        
        if env.now != 0 and (env.now%20 == 0 or env.now%(env_time -1) == 0):
            driverUtilCSV(server, foldername, filename_d, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, gen_utility, mech_name)
            generateCSV(server, foldername, filename, obf_class_size, num_riders, num_drivers, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, mech_name, count, gen_utility)
        
        # if env.now == env_time - 1:
        #     generate_regression_data(server, num_riders, num_drivers, regression_data_file, eta_tolerance, mech_number, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one)
        #     d_generate_regression_data(server, num_riders, num_drivers, d_regression_data_file, eta_tolerance, mech_number, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one)
        num_requests=int(num_riders/50)
        # num_requests=4
        if env.now<=(env_time/4):
            # print('check ',env.now,env_time)
            if server.serviceActive == False:
                server.serviceActive = True
                if env.now==0:
                    pass
                    # print('Num request are ',num_requests)
                rider_ids = np.random.randint(0, (num_riders-1), num_requests)

                for t in range(len(rider_ids)):
                    server.pendingRiders.append(rider_ids[t])
        
        yield env.timeout(1)
        print("Time: {}".format(env.now))

# extract arguments of the program
db_name = sys.argv[1]
obf_class_size = int(sys.argv[2])
num_riders = int(sys.argv[3])
num_drivers = int(sys.argv[4])
if sys.argv[5] != 'None':
    gen_utility = float(sys.argv[5])
else:
    gen_utility = None

if sys.argv[6] != 'None':
    obf_level = float(sys.argv[6])
else:
    obf_level = None

env_time = int(sys.argv[7])
eta_tolerance = int(sys.argv[8])
dd_surge_neg = sys.argv[9]
dd_surge_less_than_one = sys.argv[10]
dd_surge_more_than_one = sys.argv[11]
req_delay = int(sys.argv[12])
mech_name = sys.argv[13]
privacy_level = float(sys.argv[14])
regression_data_file = sys.argv[15]
d_regression_data_file = sys.argv[16]
mech_number = sys.argv[17]
debug_=sys.argv[18]
count=int(sys.argv[19])
exp_folder=sys.argv[20]
z_qlg=float(sys.argv[21])
g_res=float(sys.argv[22])
uniform_eta=int(sys.argv[23])
uniform_dm=int(sys.argv[24])
alpha=float(sys.argv[25])
geo_lat=float(sys.argv[26])
geo_lon=float(sys.argv[27])
uniform=int(sys.argv[28])

env = simpy.rt.RealtimeEnvironment(factor=0.01, strict=False)

env.process(simulation(env, db_name, debug_, obf_class_size, num_riders, num_drivers, gen_utility, obf_level, env_time, eta_tolerance, dd_surge_neg, 
    dd_surge_less_than_one, dd_surge_more_than_one, req_delay, mech_name, privacy_level, regression_data_file, d_regression_data_file, mech_number,
    count,exp_folder,z_qlg,g_res,alpha,geo_lat,geo_lon,uniform_eta,uniform_dm,uniform))

err_count=0
env.run(until=env_time)

# while True:
#     try:
#         env.run(until=env_time)
#         err_count=0
#     except:
#         err_count+=1
#         if err_count%100==0:
#             print('Simpy not responding err_cnt ',err_count)
#         pass
