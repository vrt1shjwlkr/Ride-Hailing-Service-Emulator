from pymongo import MongoClient
from pprint import pprint
import pymongo, random, numpy
from geopy.distance import vincenty
import datetime
import os, sys
from lppm import *
from globalvars import *
mongo = MongoClient()

'''
This function generates random data of riders and drivers.
RHSE assumes that the drivers do not obfuscate their true location, and focuses on tradeoffs between privacy and uttility experienced by the riders, hence it obfuscates the locations only of riders.
The rider objects have both real and obfuscated locations but driver objects have only real locations.

The location obfuscation mechanism should be the same as that used in rest of the simulation.

Inputs:
    lat1, lon1, lat2, lon2: geo-coordinates of the region of interest. Make sure - lat1 < lat2 and lon1 < lon2.
    regions: for discrete LPPMs, grid of regions * regions is created
    num_riders, num_drivers: number of agents to generate data for
    database_name: name of the database
    mech_name: name of the LPPM to use. choose from {planar_lap, planar_geo, exp}
    gen_util: 
    privacy_level: 
    z_qlg: unused
    g_res: grid resolution; used for discrete LPPMs
    alpha, geo_lat, geo_lon: attribute of planar geometric mechanism
    uniform: whether to distribute agents uniformly or nonuniformly.

Output:
    Database of riders and drivers managed by the mongoclient.
'''

def generate_fake_data_obf_rider(lat1, lon1, lat2, lon2, regions, num_riders, num_drivers, database_name, mech_name, gen_util, privacy_level, z_qlg, g_res,alpha,geo_lat,geo_lon, uniform=1):
    if database_name in mongo.database_names():
        mongo.drop_database(database_name)

    db = mongo[database_name]
    rider_collection = db.riders
    driver_collection = db.drivers
    
    if mech_name=='planar_lap':
        # Generate continuos locations as planar laplace mechanism is designed for infinite and continuos space

        # Generate (num_riders + num_drivers) number of latitudes and longitudes.
        lat = numpy.random.uniform(lat1, lat2, (num_riders + num_drivers))
        lon = numpy.random.uniform(lon1, lon2, (num_riders + num_drivers))

        # Generate non-uniformly distributed initial locations for drivers
        lat_drivers=np.append(np.random.uniform(lat1,lat1+(lat2-lat1)/2,int(num_drivers*0.95)),np.random.uniform(lat1+(lat2-lat1)/2,lat2,(num_drivers-int(num_drivers*0.95))))
        lat_riders=np.append(np.random.uniform(lat1,lat1+(lat2-lat1)/2,int(num_riders*0.05)),np.random.uniform(lat1+(lat2-lat1)/2,lat2,(num_riders-int(num_riders*0.05))))
           
       
        if uniform<1:
            # if uniform is set to 0, assign the  non-uniform initial locations to the driver and rider objects

            lat[:num_riders]=lat_riders # <------ If only drivers should have non-uniform initial locations, comment out this line.
            lat[num_riders:]=lat_drivers

    elif mech_name=='planar_geo' or mech_name=='exp':
        # Generate discrete locations  as planar geometric and exponential mechanisms are designed for finite but discrete space

        lat_count=round(float(vincenty([lat1,lon1], [lat2,lon1]).meters)/g_res)
        lon_count=round(float(vincenty([lat1,lon1], [lat1,lon2]).meters)/g_res)
        
        x_=(lat2-lat1)/lat_count
        y_=(lon2-lon1)/lon_count

        lat_ids=numpy.random.randint(0,lat_count+1,(num_riders))
        lon_ids=numpy.random.randint(0,lon_count+1,(num_riders))

        lat_riders=lat1+(lat_ids*x_)
        lon_riders=lon1+(lon_ids*y_)

        lat_drivers = numpy.random.uniform(lat1, lat2, (num_drivers))
        lon_drivers = numpy.random.uniform(lon1, lon2, (num_drivers))

        if uniform<1:
            lat_drivers=np.append(np.random.uniform(lat1,lat1+(lat2-lat1)/2,int(num_drivers*0.95)),np.random.uniform(lat1+(lat2-lat1)/2,lat2,(num_drivers-int(num_drivers*0.95))))
            lat_riders=np.append(np.random.uniform(lat1,lat1+(lat2-lat1)/2,int(num_riders*0.05)),np.random.uniform(lat1+(lat2-lat1)/2,lat2,(num_riders-int(num_riders*0.05))))

        lat=np.append(lat_riders,lat_drivers)
        lon=np.append(lon_riders,lon_drivers)

    
    # Apply obfuscation mechanism on the initial rider locations and truncate them to the considered region.

    dist=0
    for i in range(num_riders):
        region_row = int(regions * (lat[i] - lat1)/(lat2-lat1))
        region_col = int(regions * (lon[i] - lon1)/(lon2-lon1))
        region = regions * region_col + region_row

        [lat_obf, lon_obf]=obfuscate_loc(mech_name, [lat[i], lon[i]], gen_util, privacy_level, [lat1, lon1, lat2, lon2], g_res,alpha,geo_lat,geo_lon)
        [lat_obf, lon_obf]=truncate_loc(lat1, lon1, lat2, lon2, [lat_obf, lon_obf])
        
        # [lat_obf, lon_obf]=truncate_loc(lat1, lon1, lat1+(lat2-lat1)/2, lon2, [lat_obf, lon_obf])
        # [lat_obf, lon_obf]=truncate_loc(lat1, lon1, lat1+(lat2-lat1)/2, lon2+(lon2-lon1)/2, [lat_obf, lon_obf])

        # while check_validity(lat1, lon1, lat2, lon2, [lat_obf, lon_obf]) == False:
        #     # print('Rider obfuscated location is out of region')
        #     [lat_obf, lon_obf]=obfuscate_loc(mech_name, [lat[i], lon[i]], gen_util, privacy_level, [lat1, lon1, lat2, lon2], g_res,alpha,geo_lat,geo_lon)

        dist+=vincenty([lat_obf,lon_obf], [lat[i], lon[i]]).meters
        # print('vincenty dist ',vincenty([lat_obf,lon_obf], [lat[i], lon[i]]).meters)

        region_row_obf = int(regions * (lat_obf - lat1)/(lat2-lat1))
        region_col_obf = int(regions * (lon_obf - lon1)/(lon2-lon1))
        region_obf = regions * region_col_obf + region_row_obf

        rider_collection.insert(
                {
                    'userID': i,
                    'userType':'rider',
                    'locations': {
                        'type': "Point",
                        'coordinates': [lat[i], lon[i]]
                    },
                    'region': region,
                    "location_obf":{
                        "type":"Point",
                        "coordinates": [lat_obf, lon_obf]
                    },
                    "region_obf":region_obf
                }
            )
    
    print('Average rider obfuscation dist: ',(dist/num_riders))

    for i in range(num_drivers):
        region_row = int(regions * (lat[num_riders+i] - lat1)/(lat2-lat1))
        region_col = int(regions * (lon[num_riders+i] - lon1)/(lon2-lon1))
        region = regions * region_col + region_row

        driver_collection.insert(
                {
                    'userID': i,
                    'userType':'driver',
                    'locations': {
                        'type': "Point",
                        'coordinates': [lat[num_riders+i], lon[num_riders+i]]
                    },
                    'region': region
                }
            )

    rider_collection.create_index([('locations', pymongo.GEOSPHERE)])
    rider_collection.create_index([('location_obf', pymongo.GEOSPHERE)])
    driver_collection.create_index([('locations', pymongo.GEOSPHERE)])

# Beijing
beijing_lat1 = (116.653094)
beijing_lat2 = (116.115377)
beijing_lon1 = (39.786782)
beijing_lon2 = (40.053599)

#Paris
paris_lat1 = (48.810519)
paris_lat2 = (48.901606)
paris_lon1 = (2.275873)
paris_lon2 = (2.421079)

num_riders = sys.argv[1]
num_drivers = sys.argv[2]
regions = sys.argv[3]
database_name = sys.argv[4]
mech_name = sys.argv[5]
gen_util = float(sys.argv[6])
privacy_level = float(sys.argv[7])
z_qlg=float(sys.argv[8])
g_res=float(sys.argv[9])
uniform=float(sys.argv[10])
alpha=float(sys.argv[11])
geo_lat=float(sys.argv[12])
geo_lon=float(sys.argv[13])

generate_fake_data_obf_rider(paris_lat1, paris_lon1, paris_lat2, paris_lon2, int(regions), int(num_riders), int(num_drivers), database_name, mech_name, gen_util, privacy_level,z_qlg,g_res,alpha,geo_lat,geo_lon,uniform=uniform)