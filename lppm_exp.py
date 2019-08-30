from __future__ import division
import random
# from lppm_planar_lap import *
import numpy as np
from geopy.distance import vincenty

# reference: https://people.eecs.berkeley.edu/~jordan/courses/260-spring10/lectures/lecture17.pdf

def add_exp_noise(location, eps, region, g_res):

    lat1=region[0]
    lon1=region[1]
    lat2=region[2]
    lon2=region[3]

    lat=location[0]
    lon=location[1]

    lat_count=int(float(vincenty([lat1,lon1], [lat2,lon1]).meters)/g_res)
    lon_count=int(float(vincenty([lat1,lon1], [lat1,lon2]).meters)/g_res)

    x_=(lat2-lat1)/lat_count
    y_=(lon2-lon1)/lon_count

    norm=0
    for i in range(lat_count+1):
        grid_lat=lat1+x_*i
        for j in range(lon_count+1):
            grid_lon=lon1+x_*j
            norm+= np.exp(-0.5*eps*vincenty(location,[grid_lat,grid_lon]).meters)

    grid_prob=[]
    
    grid=np.arange((lat_count+1)*(lon_count+1))

    for i in range(lat_count+1):
        grid_lat=lat1+x_*i
        for j in range(lon_count+1):
            grid_lon=lon1+x_*j
            grid_prob.append(np.exp(-0.5*eps*vincenty(location,[grid_lat,grid_lon]).meters)/norm)

    idx=np.random.choice(grid,p=grid_prob)

    lat_idx=int(idx/(lat_count+1))
    lon_idx=(idx%(lon_count+1))
    #print(idx, lat_idx, lon_idx)

    return [round(lat1+lat_idx*x_,6), round(lon1+lon_idx*y_,6)]