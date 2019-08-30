import numpy as np
import random
from rhse_util import *

def map_to_grid(region,location,g_res):
	lat1=region[0]
	lon1=region[1]
	lat2=region[2]
	lon2=region[3]

	lat_count=int(float(vincenty([lat1,lon1], [lat2,lon1]).meters)/g_res)
	lon_count=int(float(vincenty([lat1,lon1], [lat1,lon2]).meters)/g_res)
	
	x_=(lat2-lat1)/lat_count
	y_=(lon2-lon1)/lon_count

	lat=location[0]
	lon=location[1]

	lat_idx=int((lat-lat1)/x_)+(np.random.random()>0.5)
	lon_idx=int((lon-lon1)/y_)+(np.random.random()>0.5)

	location[0]=lat1+lat_idx*x_
	location[1]=lon1+lon_idx*y_

	return location

def calculate_pg_normalizer(l,r,g_res):
	alpha=0
	for i in range(500):
		for j in range(500):
			alpha+=np.exp((-np.log(l)*g_res/(r*1000))*np.sqrt(i**2+j**2))
	print('Normalizer for eps {} is {}'.format(np.log(l)/(r*1000),(1/alpha)))
	return (1/alpha)


def get_geo_noise(location,eps,g_res,alpha,geo_lat,geo_lon):
	# choose random number between [0,1]
	pos_lat=location[0]
	pos_lon=location[1]

	z=random.random()
	# print(z)
	
	p=alpha
	n=1
	pairs=[[0,0]]
	while p<=z:
		t,pairs=sumSquare(n)
		if t:
			for pair in pairs:
				if pair[0]!=pair[1]:
					p+= 2*alpha*np.exp((-eps*g_res)*np.sqrt(n))
				else:
					p+= alpha*np.exp((-eps*g_res)*np.sqrt(n))
		n+=1
	# print(pairs)
	j=np.random.randint(len(pairs),size=1)[0]
	dist=g_res*np.sqrt(n-1)
	# print('normal dist ',dist)
	# lat=pos_lat+pairs[j][0]*geo_lat
	# lon=pos_lon+pairs[j][1]*geo_lon

	return pairs[j],dist
	


def add_geo_noise(location,region,eps,g_res,alpha,geo_lat,geo_lon):
	pair,r=get_geo_noise(location,eps,g_res,alpha,geo_lat,geo_lon)

	if pair[0]==0:
		theta=np.pi/2
	else:
		theta=np.arctan(pair[1]/pair[0])

	[lat,lon]=add_vector_to_pos(location[0], location[1], r, theta)
	# print('distance :',vincenty([lat,lon], location).meters)
	return map_to_grid(region,[lat,lon],g_res)

	



def sumSquare(n):
	s = {}
	pairs=[]
	for i in range(n):
		if i**2 > n:
			break

		if n ==1:
			return True,[[0,1]]

		# store square value in hashmap
		s[i**2] = 1
		
		if (n - i**2) in s.keys():
			# print((n - i**2)**(0.5), i)
			pairs.append([(n - i**2)**(0.5), i])
		
			# return True, (n-i**2)**(0.5), i

	if len(pairs):
		# print(pairs)
		return True,pairs
	else:
		return False,pairs
	
	return False, None, None