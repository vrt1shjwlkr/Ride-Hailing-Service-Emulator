from __future__ import division
import os, sys, logging, random
from realLocationUtil import *
from driver_decision import *
from rhse_util import *
from globalvars import *
import numpy as np



def calculate_estimate_adaptive_tolerance(driver_list, surge_factor, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, server, uniform_eta=True):
    estimated_eta = None
    while estimated_eta == None:
        for i in range(len(driver_list)):
            
            driver_id = driver_list[i][0]
            
            location = list(server.database.drivers.distinct("locations",{"userID":driver_id}))
            driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
            in_spl_zone=check_driver_loc(driverLocation)

            driver_eta = driver_list[i][1]*5 if (not uniform_eta and in_spl_zone) else driver_list[i][1]
            driver = server.driverObjects[driver_id]
            driver_tolerance = driver.tolerance if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
            # print('Estimating ETA -- Driver {} ETA tolerance {}'.format(driver_id, driver_tolerance))
            diff = driver_tolerance - driver_eta

            if driver_eta < driver_tolerance:
                estimated_eta = driver_eta

            elif surge_factor == -1:
                if dd_surge_neg == 'hard':
                    estimated_eta = driver_eta if diff >= 0 else None
                elif dd_surge_neg == 'exp':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/100)) else None
                elif dd_surge_neg == 'log':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/10)) else None

            elif surge_factor > 1:
                if dd_surge_more_than_one == 'hard':
                    estimated_eta = driver_eta if diff >= 0 else None
                elif dd_surge_more_than_one == 'exp':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/100)) else None
                elif dd_surge_more_than_one == 'log':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/10)) else None
            
            else:
                if dd_surge_less_than_one == 'hard':
                    estimated_eta = driver_eta if diff >= 0 else None
                elif dd_surge_less_than_one == 'exp':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/100)) else None
                elif dd_surge_less_than_one == 'log':
                    estimated_eta = driver_eta if (random.random() < math.exp(diff/10)) else None

            if estimated_eta == None:
                # this driver did not accept increase req_refusal_count for her
                driver.req_refusal_count += 1
                # print('Estimating ETA -- Driver {} refused; increasing req_refusal_count to {}'.format(driver_id, driver.req_refusal_count))
            else:
                driver.req_refusal_count=0
                driver.surge_factor=surge_factor
                # print('Estimating ETA -- Driver {} refused; resetting req_refusal_count to {}'.format(driver_id, driver.req_refusal_count))
                return driver.id, estimated_eta, driver_tolerance

def calculate_estimate(driver_list, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server):
    p = 0
    estimated_eta = 0
    for i in range(len(driver_list)):
        driver_id = driver_list[i][0]
        driver_eta = driver_list[i][1]
        driver_tolerance = server.driverObjects[driver_id].tolerance 
        diff = driver_tolerance - driver_eta
        # print(driver_eta, diff)
        if driver_eta < driver_tolerance or surge_factor == -1:
            p = 1
            estimated_eta = driver_eta
            break
        elif surge_factor > 1:
            if dd_surge_more_than_one == 'hard':
                p += math.exp(diff/10)
                estimated_eta += math.exp(diff/10) * driver_eta
            elif dd_surge_more_than_one == 'exp':
                p += math.exp(diff/100)
                estimated_eta += math.exp(diff/1000) * driver_eta
            elif dd_surge_more_than_one == 'log':
                p += math.exp(diff/1000)
                estimated_eta += math.exp(diff/100) * driver_eta
        else:
            if dd_surge_less_than_one == 'hard':
                p += math.exp(diff/1)
                estimated_eta += math.exp(diff/1) * driver_eta
            elif dd_surge_less_than_one == 'exp':
                p += math.exp(diff/10)
                estimated_eta += math.exp(diff/10) * driver_eta
            elif dd_surge_less_than_one == 'log':
                p += math.exp(diff/100)
                estimated_eta += math.exp(diff/100) * driver_eta
    if p != 0:
        # print('ETA_estimate is {} {} {}'.format(estimated_eta/p, estimated_eta, p))
        return (estimated_eta/p)
    else:
        # print('Drivers are too far!!! Assuming ETA to be ETA of the closest driver {}'.format(driver_list[0][1]))
        return (driver_list[0][1])


def choose_driver(driver_list, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server):
    for i in range(len(driver_list)):
        driver_id = driver_list[i][0]
        driver_eta = driver_list[i][1]
        driver_tolerance = server.driverObjects[driver_id].tolerance 
        diff = driver_tolerance - driver_eta

        if driver_eta < driver_tolerance:
            return driver_id, driver_eta

        elif surge_factor == -1:
            return driver_id, driver_eta

        elif surge_factor > 1:
            if dd_surge_more_than_one == 'hard':
                if random.random() < math.exp(diff/10):
                    return driver_id, driver_eta
            elif dd_surge_more_than_one == 'exp':
                if random.random() < math.exp(diff/100):
                    return driver_id, driver_eta
            elif dd_surge_more_than_one == 'log':
                if random.random() < math.exp(diff/1000):
                    return driver_id, driver_eta

        else:
            if dd_surge_less_than_one == 'hard':
                if random.random() < math.exp(diff/1):
                    return driver_id, driver_eta
            elif dd_surge_less_than_one == 'exp':
                if random.random() < math.exp(diff/10):
                    return driver_id, driver_eta
            elif dd_surge_less_than_one == 'log':
                if random.random() < math.exp(diff/100):
                    return driver_id, driver_eta
    
    d_index = int(round(abs(np.random.normal(0, (len(driver_list)/2), 1)[0])))
    while d_index > len(driver_list)-1:
        d_index = int(round(abs(np.random.normal(0, (len(driver_list)/2), 1)[0])))

    return driver_list[d_index][0], driver_list[d_index][1]

'''
This function calculates worst case utility loss for the incomplete rides
'''

def etaEstimate(server, env_time, database, uniform_eta):
    collection = database.drivers
    dd_surge_neg=server.driverObjects[0].dd_surge_neg
    dd_surge_less_than_one=server.driverObjects[0].dd_surge_less_than_one
    dd_surge_more_than_one=server.driverObjects[0].dd_surge_more_than_one

    if not len(server.riderObjects):
        print('****No rides incomplete****')
        return 0

    for i in range(len(server.riderObjects)):
        rider = server.riderObjects[i]
        # estimate for driver ETA around real location
        if rider.first_req_time and not rider.real_ride_start_time:
            surge_factor = calculate_surge(rider, True)
            if rider.real_location_drivers:
                # driver_id, driver_eta = choose_driver(rider.real_location_drivers, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server)
                driver_id, driver_eta, rider.real_accept_eta_tolerance = calculate_estimate_adaptive_tolerance(rider.real_location_drivers, surge_factor, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, server, uniform_eta)
                rider.est_real_ride_start_time = (env_time - rider.first_req_time) * rider.req_delay + driver_eta
                rider.real_accept_eta = driver_eta + rider.numOfExtraTrials*EXTRA_TRIAL_PENALTY

                server.driverObjects[driver_id].real_acc_rides += 1
                server.driverObjects[driver_id].cal_earning(True, rider.rideRequestLocation, rider.rideDestination, driver_eta)
                # print('Rider {} has already found drivers; Worst case ETA is {}'.format(rider.id, rider.est_real_ride_start_time))
                real_ride_complete = 2
            else:
                penalty_dist=rider.max_search_distance+500
                while True:
                    real_list = list(collection.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.rideRequestLocation},"$maxDistance":penalty_dist}}}))
                    if real_list:
                        if rider.real_num_of_trials > 1:
                            rider.real_num_of_trials += 1
                        rider.real_location_drivers = sortDrivers(real_list, rider, True)
                        # driver_id, driver_eta = choose_driver(rider.real_location_drivers, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server)
                        driver_id, driver_eta, rider.real_accept_eta_tolerance = calculate_estimate_adaptive_tolerance(rider.real_location_drivers, surge_factor, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, server, uniform_eta)
                        rider.est_real_ride_start_time = ((env_time - rider.first_req_time) * rider.req_delay) + driver_eta
                        rider.real_accept_eta = driver_eta + rider.numOfExtraTrials*EXTRA_TRIAL_PENALTY

                        server.driverObjects[driver_id].real_acc_rides += 1
                        server.driverObjects[driver_id].cal_earning(True, rider.rideRequestLocation, rider.rideDestination, driver_eta)
                        break
                    else:
                        penalty_dist += 1000
                print('Real loc: Rider {} had no drivers in {}m, worst case ETA {}, search range {}'.format(rider.id, rider.max_search_distance, rider.est_real_ride_start_time, penalty_dist))
                real_ride_complete = 2
        else:
            real_ride_complete = 1
            pass

        if rider.first_req_time and not rider.obf_ride_start_time:
        	# estimate for driver ETA around obf location
            surge_factor = calculate_surge(rider, False)
            if rider.obf_loc_drivers:
                # driver_id, driver_eta = choose_driver(rider.obf_loc_drivers, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server)
                driver_id, driver_eta, rider.obf_accept_eta_tolerance = calculate_estimate_adaptive_tolerance(rider.obf_loc_drivers, surge_factor, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, server, uniform_eta)
                rider.est_obf_ride_start_time = ((env_time - rider.obf_loc_processing_start) * rider.req_delay) + driver_eta
                rider.obf_accept_eta = driver_eta + rider.numOfExtraTrials*EXTRA_TRIAL_PENALTY

                server.driverObjects[driver_id].obf_acc_rides += 1
                server.driverObjects[driver_id].cal_earning(False, rider.obfuscatedReqeustLocation, rider.rideDestination, driver_eta)
                # print('Rider {} has already found drivers; Worst case ETA is {}'.format(rider.id, rider.est_obf_ride_start_time))
                obf_ride_complete = 2
            else:
                penalty_dist=rider.max_search_distance+500
                while True:
                    obf_list = list(collection.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.obfuscatedReqeustLocation},"$maxDistance":penalty_dist}}}))
                    if obf_list:
                        if rider.num_of_trials > 1:
                            rider.num_of_trials += 1
                        rider.obf_loc_drivers = sortDrivers(obf_list, rider, False)
                        # driver_id, driver_eta = choose_driver(rider.obf_loc_drivers, surge_factor, dd_surge_less_than_one, dd_surge_more_than_one, server)
                        driver_id, driver_eta, rider.obf_accept_eta_tolerance = calculate_estimate_adaptive_tolerance(rider.obf_loc_drivers, surge_factor, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, server, uniform_eta)
                        
                        if rider.obf_loc_processing_start:
                            # print('Rider {} Obfuscated location processing already started at {}'.format(rider.id, rider.obf_loc_processing_start))
                            rider.est_obf_ride_start_time = ((env_time - rider.obf_loc_processing_start) * rider.req_delay) + driver_eta
                            rider.obf_accept_eta = driver_eta + rider.numOfExtraTrials*EXTRA_TRIAL_PENALTY
                            break
                        else:
                            # print('Rider {} Obfuscated location processing not started first req time is {}'.format(rider.id, rider.first_req_time))
                            rider.est_obf_ride_start_time = ((env_time - rider.first_req_time) * rider.req_delay) + driver_eta
                            rider.obf_accept_eta = driver_eta + rider.numOfExtraTrials*EXTRA_TRIAL_PENALTY
                            break

                        server.driverObjects[driver_id].obf_acc_rides += 1
                        server.driverObjects[driver_id].cal_earning(False, rider.obfuscatedReqeustLocation, rider.rideDestination, driver_eta)
                    else:
                        penalty_dist += 1000
                print('Obfuscated loc: Rider {} had no drivers in {}m, worst case ETA {}, search range {}'.format(rider.id,rider.max_search_distance, rider.est_obf_ride_start_time, penalty_dist))
                obf_ride_complete = 2
        else:
            obf_ride_complete = 1
            pass

        if rider.est_obf_ride_start_time and rider.est_real_ride_start_time:
            expected_gen_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*rider.euclidean_dist
            expected_tai_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*(rider.est_obf_ride_start_time - rider.est_real_ride_start_time)
            rider.rideDetails.append([rider.num_of_trials, rider.numOfExtraTrials, rider.real_num_of_trials, obf_ride_complete, real_ride_complete, rider.first_req_time, rider.obf_loc_req_accept_time, rider.est_obf_ride_start_time, rider.real_loc_req_accept_time, rider.est_real_ride_start_time, 1000 * rider.gen_utility, (rider.est_obf_ride_start_time - rider.est_real_ride_start_time), rider.num_real_loc_drivers, rider.avg_etas_real_loc_drivers, rider.avg_real_acc_rate, rider.avg_real_surge, rider.num_obf_loc_drivers, rider.avg_etas_obf_loc_drivers, rider.avg_obf_acc_rate, rider.avg_obf_surge, rider.obf_real_eta, rider.privacy_level, rider.min_eta_real_loc_drivers, rider.min_eta_obf_loc_drivers, rider.real_accept_eta_tolerance, rider.obf_accept_eta_tolerance, rider.real_accept_eta, rider.obf_accept_eta, rider.euclidean_dist, expected_gen_ql, expected_tai_ql])
            rider.est_real_ride_start_time = None
            rider.est_obf_ride_start_time = None
        
        elif rider.est_real_ride_start_time and not rider.est_obf_ride_start_time:
            expected_gen_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*rider.euclidean_dist
            expected_tai_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*(rider.obf_ride_start_time - rider.est_real_ride_start_time)
            rider.rideDetails.append([rider.num_of_trials, rider.numOfExtraTrials, rider.real_num_of_trials, obf_ride_complete, real_ride_complete, rider.first_req_time, rider.obf_loc_req_accept_time, rider.obf_ride_start_time, rider.real_loc_req_accept_time, rider.est_real_ride_start_time, 1000 * rider.gen_utility, (rider.obf_ride_start_time - rider.est_real_ride_start_time), rider.num_real_loc_drivers, rider.avg_etas_real_loc_drivers, rider.avg_real_acc_rate, rider.avg_real_surge, rider.num_obf_loc_drivers, rider.avg_etas_obf_loc_drivers, rider.avg_obf_acc_rate, rider.avg_obf_surge, rider.obf_real_eta, rider.privacy_level, rider.min_eta_real_loc_drivers, rider.min_eta_obf_loc_drivers, rider.real_accept_eta_tolerance, rider.obf_accept_eta_tolerance, rider.real_accept_eta, rider.obf_accept_eta, rider.euclidean_dist, expected_gen_ql, expected_tai_ql])
            rider.est_real_ride_start_time = None
        
        elif rider.est_obf_ride_start_time and not rider.est_real_ride_start_time:
            expected_gen_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*rider.euclidean_dist
            expected_tai_ql=((math.log(rider.privacy_level)/(rider.gen_utility*1000))**2)*(math.exp(-math.log(rider.privacy_level)*rider.euclidean_dist/(rider.gen_utility*1000)))*(rider.est_obf_ride_start_time - rider.real_ride_start_time)
            rider.rideDetails.append([rider.num_of_trials, rider.numOfExtraTrials, rider.real_num_of_trials, obf_ride_complete, real_ride_complete, rider.first_req_time, rider.obf_loc_req_accept_time, rider.est_obf_ride_start_time, rider.real_loc_req_accept_time, rider.real_ride_start_time, 1000 * rider.gen_utility, (rider.est_obf_ride_start_time - rider.real_ride_start_time), rider.num_real_loc_drivers, rider.avg_etas_real_loc_drivers, rider.avg_real_acc_rate, rider.avg_real_surge, rider.num_obf_loc_drivers, rider.avg_etas_obf_loc_drivers, rider.avg_obf_acc_rate, rider.avg_obf_surge, rider.obf_real_eta, rider.privacy_level, rider.min_eta_real_loc_drivers, rider.min_eta_obf_loc_drivers, rider.real_accept_eta_tolerance, rider.obf_accept_eta_tolerance, rider.real_accept_eta, rider.obf_accept_eta, rider.euclidean_dist, expected_gen_ql, expected_tai_ql])
            rider.est_obf_ride_start_time = None

