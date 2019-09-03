import simpy, os, datetime, random, simplejson, urllib, operator, logging
from pymongo import MongoClient
from realLocationUtil import *
from distance_apis import *
from driver_decision import *
from lppm import * 

class Server:
    def __init__(self, database, debug_,z_qlg):
        self.database = database
        self.serviceActive = False
        self.pendingRiders = []
        self.riderObjects = []
        self.driverObjects = []
        self.z_qlg=z_qlg
        
        regionDetails = []
        with open('regionDetails.txt', 'r') as rf:
            for line in rf:
                regionDetails.append(line.split('=')[-1])
            self.regions = int(regionDetails[0])
            self.regionLat1 = float(regionDetails[1])
            self.regionLat2 = float(regionDetails[2])
            self.regionLon1 = float(regionDetails[3])
            self.regionLon2 = float(regionDetails[4])

    def getDrivers(self, env, collection, rider, obf_loc):
        if obf_loc:
            obf_list = list(collection.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.obfuscatedReqeustLocation},"$maxDistance":rider.obf_last_match_distance}}}))
            # print(obf_list)
            return obf_list
        else:
            real_list = list(collection.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.rideRequestLocation},"$maxDistance":rider.real_last_match_distance}}}))
            obf_list = list(collection.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.obfuscatedReqeustLocation},"$maxDistance":rider.obf_last_match_distance}}}))
            if obf_list:
                rider.obf_no_drivers_time = env.now - rider.first_req_time

            # print(obf_list, real_list)
            return real_list

    def findClosestDriver(self, obf_loc_drivers, rider):
        least_time = 1000000
        drivers_id_eta = {}
        destinations = []
        # print(len(obf_loc_drivers))
        for i in range(len(obf_loc_drivers)):
            destinations.append([obf_loc_drivers[i].get('locations').get('coordinates')[0], obf_loc_drivers[i].get('locations').get('coordinates')[1]])

        etas, distances = distance_api(rider.rideRequestLocation, destinations)

        for i in range(len(etas)):
            drivers_id_eta[obf_loc_drivers[i].get('userID')] = etas[i]

        if not drivers_id_eta:
            print('None of the drivers can reach rider via road, please try again later')
            return None

        sorted_drivers = sorted(drivers_id_eta.items(), key=operator.itemgetter(1))
        # print(sorted_drivers)
        # Calculate the regression parameters
        rider.num_obf_loc_drivers += len(sorted_drivers)

        if rider.avg_obf_surge:
            rider.avg_obf_surge += calculate_surge(rider, False)
        else:
            rider.avg_obf_surge = calculate_surge(rider, False)

        rider.min_eta_obf_loc_drivers += sorted_drivers[0][1]

        for i in range(len(sorted_drivers)):
                rider.avg_etas_obf_loc_drivers += sorted_drivers[i][1]
                if self.driverObjects[sorted_drivers[i][0]].obf_acc_rate:
                    rider.avg_obf_acc_rate += self.driverObjects[sorted_drivers[i][0]].obf_acc_rate
                else:
                    rider.avg_obf_acc_rate += 0

        # this obf_loc_drivers contains driverIDs sorted by ETA
        while sorted_drivers:
            driver_id = sorted_drivers[0][0]
            driver_eta = sorted_drivers[0][1]
            sorted_drivers.pop(0)
            if not self.driverObjects[driver_id].matchedRider:
                break
            else:
                driver_id = None
                driver_eta = None
        
        if driver_id:
            rider.obf_loc_drivers = sorted_drivers
            # print("Rider {}: Closest driver with ID {} and state {} will reach in {}".format(rider.id, driver_id, self.driverObjects[driver_id].state, driver_eta))
            self.driverObjects[driver_id].matchedRider = rider
            rider.driver_eta = driver_eta
            
            return self.driverObjects[driver_id]
        else:
            return None


    def findDrivers(self, rider, env):
        dbDrivers=self.database.drivers
        while True:
            # processing real location
            if rider.real_loc_req_accept_time == None:
                rider.real_loc_req = True
                real_loc_drivers = self.getDrivers(env, dbDrivers, rider, False)
                
                if len(real_loc_drivers):
                    #print('Real Location  Rider {} Found drivers at {} meter radius'.format(rider.id, rider.real_last_match_distance))
                    return realLocationUtility(real_loc_drivers, rider, env)
                else:
                    # rider.real_last_match_distance += 500
                    if rider.real_last_match_distance == rider.max_search_distance:
                        print('Real Location Rider {} No drivers around!'.format(rider.id))
                        return None

            elif not rider.real_loc_req:
                if rider.obf_loc_processing_start == None:
                    rider.obf_loc_processing_start = env.now - rider.obf_no_drivers_time
                
                # print('Rider {} requesting using obf_loc processing start time {}'.format(rider.id, rider.obf_loc_processing_start))
                obf_loc_drivers = self.getDrivers(env, dbDrivers, rider, True)
                
                if not len(obf_loc_drivers):
                    # rider.obf_last_match_distance += 500
                    if rider.obf_last_match_distance == rider.max_search_distance:
                        print ('Obfuscated Location Rider {} No drivers around!'.format(rider.id))
                        self.serviceActive = False
                        return None
                else:
                    # Send corresponding driver object
                    print ('Obfuscated Location Rider {} Found {} drivers at {} meter radius'.format(rider.id, len(obf_loc_drivers), rider.obf_last_match_distance))
                    return self.findClosestDriver(obf_loc_drivers,rider)


    def updateMongoDriver(self, driver):
        if self.serviceActive:
            self.serviceActive = False

        # Following code is for greedy remapping experiment in Figure 6
        if driver.uniform==0:
            z=random.random()
            if z<0.95:
                driver.rideDestination[0]=np.random.uniform(self.regionLat1,self.regionLat1+((self.regionLat2-self.regionLat1)/2),1)[0]
            else:
                driver.rideDestination[0]=np.random.uniform(self.regionLat1+((self.regionLat2-self.regionLat1)/2),self.regionLat2,1)[0]
        driver.rideDestination[1]=np.random.uniform(self.regionLon1,self.regionLon1+((self.regionLon2-self.regionLon1)/2),1)[0]

        region_row = int(self.regions * ((driver.rideDestination[0] - self.regionLat1)/(self.regionLat2-self.regionLat1)))
        region_col = int(self.regions * ((driver.rideDestination[1] - self.regionLon1)/(self.regionLon2-self.regionLon1)))
        region = (self.regions * region_col) + region_row
        dbDrivers=self.database.drivers
        dbDrivers.update(
            {"userID":driver.id},
            {
                "userID":driver.id,
                "userType":"driver",
                "region":region,
                "locations":{
                    "type":"Point",
                    "coordinates":[driver.rideDestination[0], driver.rideDestination[1]]
                }
            }
        )

    
    def map_to_grid(self,rider):
        lat_count=round(float(vincenty([self.regionLat1,self.regionLon1], [self.regionLat2,self.regionLon1]).meters)/rider.g_res)
        lon_count=round(float(vincenty([self.regionLat1,self.regionLon1], [self.regionLat1,self.regionLon2]).meters)/rider.g_res)
        
        x_=(self.regionLat2-self.regionLat1)/lat_count
        y_=(self.regionLon2-self.regionLon1)/lon_count

        lat=rider.rideDestination[0]
        lon=rider.rideDestination[1]

        lat_idx=int((lat-self.regionLat1)/x_)+(np.random.random()>0.5)
        lon_idx=int((lon-self.regionLon1)/y_)+(np.random.random()>0.5)
        
        rider.rideDestination[0]=self.regionLat1+lat_idx*x_
        rider.rideDestination[1]=self.regionLon1+lon_idx*y_

    
    def update_mongo_rider(self, rider):
        if self.serviceActive:
            self.serviceActive = False

        if rider.mech_name=='planar_geo' or rider.mech_name=='exp':
            self.map_to_grid(rider)

        region_row = int(self.regions * ((rider.rideDestination[0] - self.regionLat1)/(self.regionLat2-self.regionLat1)))
        region_col = int(self.regions * ((rider.rideDestination[1] - self.regionLon1)/(self.regionLon2-self.regionLon1)))
        region = (self.regions * region_col) + region_row
        
        if rider.obf_level == None:
            if rider.gen_utility == None:
                print('No input for obfuscation; exiting')
                sys.exit()
            
            [lat_obf, lon_obf]=obfuscate_loc(rider.mech_name, rider.rideDestination, rider.gen_utility, rider.privacy_level, [self.regionLat1,self.regionLon1,self.regionLat2,self.regionLon2], rider.g_res,rider.alpha,rider.geo_lat,rider.geo_lon)
            
            if not rider.greedy_remap:
                [lat_obf, lon_obf]=truncate_loc(self.regionLat1, self.regionLon1, self.regionLat2, self.regionLon2, [lat_obf, lon_obf])
            else:
                [lat_obf, lon_obf]=truncate_loc(self.regionLat1, self.regionLon1, self.regionLat1+(self.regionLat2-self.regionLat1)/2, self.regionLon2, [lat_obf, lon_obf])

        region_row_obf = int(self.regions * (lat_obf - self.regionLat1)/(self.regionLat2-self.regionLat1))
        region_col_obf = int(self.regions * (lon_obf - self.regionLon1)/(self.regionLon2-self.regionLon1))
        region_obf = self.regions * region_col_obf + region_row_obf

        # print('Ride complete: updating rider location to {} {} and obfuscated to {} {}'.format(rider.rideDestination[0], rider.rideDestination[1], lat_obf, lon_obf))

        dbRiders=self.database.riders
        dbRiders.update(
            {"userID":rider.id},
            {
                "userID":rider.id,
                "userType":"rider",
                "region":region,
                "locations":{
                    "type":"Point",
                    "coordinates":[rider.rideDestination[0], rider.rideDestination[1]]
                },
                "location_obf":{
                    "type":"Point",
                    "coordinates": [lat_obf, lon_obf]
                },
                "region_obf": region_obf
            }
        )

    def run(self, env):
        while True:
            for i in range(len(self.driverObjects)):
                if self.driverObjects[i].blocked:
                    self.driverObjects[i].block_clock -= 1
                    if self.driverObjects[i].block_clock == 0:
                        self.driverObjects[i].blocked = False
                        print('Unblocking driver {} at time {}'.format(self.driverObjects[i].id, env.now))

            while len(self.pendingRiders):
                # Create rider class for the rider
                rider = self.riderObjects[self.pendingRiders[0]]

                if rider.service_active == False and (rider.retry_timer == None or rider.retry_timer == env.now):
                    rider.retry_timer = None
                    rider.state = LOOKING_FOR_DRIVER
                    rider.service_active = True
                    rider.details_obf_drivers = None
                    rider.details_real_drivers = None

                    if rider.num_of_trials == 0:
                        rider.num_of_trials += 1

                    if rider.real_num_of_trials == 0:
                        rider.real_num_of_trials += 1

                    print('Rider {} requested a ride, Obfuscated location trial number {} Real location trial number {}'.format(rider.id, rider.num_of_trials, rider.real_num_of_trials))

                else:
                    if rider.matchedDriver:
                        print('Rider {} requested a ride, but service is already active and waiting for Driver {}'.format(rider.id, rider.matchedDriver.id))
                    elif not rider.matchedDriver :
                        print('Rider {} requested a ride, but service is already active and searching for driver'.format(rider.id))
                    else:
                        print('Rider {} retry timer is still running'.format(rider.id))                
                self.pendingRiders.pop(0)
            
            yield env.timeout(1)