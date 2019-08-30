from __future__ import division
import simpy, os, datetime, random, simplejson, urllib, operator, logging, sys
from pymongo import MongoClient
from distance_apis import *
from driver_decision import *

'''
This function takes a list of drivers and rider objects as inputs and outputs sorted list of driver based on
real location of the rider object.
'''

def sortDrivers(drivers_list, rider, real_loc_req):
    destinations = []
    # print('Rider {} requesting; sorting drivers'.format(rider.id))
    least_time = 1000000
    drivers_id_eta = {}
    for i in range(len(drivers_list)):
        destinations.append([drivers_list[i].get('locations').get('coordinates')[0], drivers_list[i].get('locations').get('coordinates')[1]])

    etas, distances = distance_api(rider.rideRequestLocation, destinations)

    for i in range(len(etas)):
        drivers_id_eta[drivers_list[i].get('userID')] = etas[i]
    
    if not drivers_id_eta:
        print('None of the drivers can reach rider via road, please try again later')
        return None

    sorted_drivers = sorted(drivers_id_eta.items(), key=operator.itemgetter(1))
    
    if real_loc_req:
        rider.num_real_loc_drivers += len(sorted_drivers)

        if rider.avg_real_surge:
            rider.avg_real_surge += calculate_surge(rider, True)
        else:
            rider.avg_real_surge = calculate_surge(rider, True)

        rider.min_eta_real_loc_drivers += sorted_drivers[0][1]

        for i in range(len(sorted_drivers)):
            rider.avg_etas_real_loc_drivers += sorted_drivers[i][1]
            if rider.server.driverObjects[sorted_drivers[i][0]].real_acc_rate:
                rider.avg_real_acc_rate += rider.server.driverObjects[sorted_drivers[i][0]].real_acc_rate
            else:
                rider.avg_real_acc_rate += 0
    else:
        rider.num_obf_loc_drivers += len(sorted_drivers)

        if rider.avg_obf_surge:
            rider.avg_obf_surge += calculate_surge(rider, False)
        else:
            rider.avg_obf_surge = calculate_surge(rider, False)

        rider.min_eta_obf_loc_drivers += sorted_drivers[0][1]

        for i in range(len(sorted_drivers)):
            rider.avg_etas_obf_loc_drivers += sorted_drivers[i][1]
            if rider.server.driverObjects[sorted_drivers[i][0]].obf_acc_rate:
                rider.avg_obf_acc_rate += rider.server.driverObjects[sorted_drivers[i][0]].obf_acc_rate
            else:
                rider.avg_obf_acc_rate += 0
    return sorted_drivers




'''
This function handles sending very first request to closest driver around real location of rider.
'''

def realLocationUtility(real_location_drivers, rider, env):
    rider.real_location_drivers = sortDrivers(real_location_drivers, rider, True)
    if rider.real_location_drivers == None:
        print('Real Location Rider {} - No drivers can reach the rider'.format(rider.id))
        return None
    while len(rider.real_location_drivers):
        # check if the driver is free and not serving any other rider
        if rider.server.driverObjects[rider.real_location_drivers[0][0]].state == WAITING_FOR_RIDE_REQ and rider.server.driverObjects[rider.real_location_drivers[0][0]].matchedRider == None:
            # send rider to a driver as a matched_rider
            print('Real Location Rider {} sent request to Driver {} with ETA {}'.format(rider.id, rider.real_location_drivers[0][0], rider.real_location_drivers[0][1]))
            rider.server.driverObjects[rider.real_location_drivers[0][0]].matchedRider = rider
            rider.driver_eta = rider.real_location_drivers[0][1]
            return rider.server.driverObjects[rider.real_location_drivers[0][0]]
        else:
            print('Real Location Rider {} - Driver {} already serving someone, trying next available Driver'.format(rider.id, rider.real_location_drivers[0][0]))
            rider.real_location_drivers.pop(0)

    # If all the drivers in the list of real location are busy -
    if not rider.real_loc_req:
        print('Real Location Rider {} - No more drivers in available list, lets try obfuscated location'.format(rider.id))
        return None

