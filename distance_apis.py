import simplejson, time
from geopy.distance import vincenty
from urllib2 import urlopen


def osrm_distance(source, destination):
    source_str = str(source[1]) + ',' + str(source[0])
    dst_str = str(destination[1]) + ',' + str(destination[0])
    url = 'http://router.project-osrm.org/table/v1/driving/{};{}?sources=0'.format(source_str, dst_str) 
    # result = simplejson.load(urllib.request.urlopen(url))
    result = simplejson.load(urlopen(url))
    while result.get('code') != 'Ok':
        print(url, result)
        time.sleep(10)
        result = simplejson.load(urllib.request.urlopen(url))
    distance_matrix = result.get('durations')
    return distance_matrix[0][1]

def osrm_api(source, destinations):
    
    etas = []
    distances = []
    destinations_str = ''

    # NOTE: in this API coordinates' order is [longitude, latitude]
    source_str = str(source[1]) + ',' + str(source[0])
    for i in range(len(destinations)):
        destination = str(destinations[i][1]) + ',' + str(destinations[i][0])
        destinations_str += destination + ';'
    destinations_str = destinations_str[:-1]
    url = 'http://router.project-osrm.org/table/v1/driving/{};{}?sources=0'.format(source_str, destinations_str)
    
    # result = simplejson.load(urllib.request.urlopen(url))
    # try:
    #     result = simplejson.load(urlopen(url))
    # except:
    #     print('something went wrong!!')
    
    result={'code':'NOk'}

    while result.get('code') != 'Ok':
        # result = simplejson.load(urllib.request.urlopen(url))
        try:
            result = simplejson.load(urlopen(url))
        except:
            print('something went wrong!!')
            result={'code':'NOk'}
            time.sleep(10)
    distance_matrix = result.get('durations')

    for i in range(len(distance_matrix)):
        for j in range(len(distance_matrix[i])-1):
            etas.append(distance_matrix[i][j+1])

    source_lat = source[0]
    source_lon = source[1]
    for i in range(len(destinations)):
        destination_lat = destinations[i][0]
        destination_lon = destinations[i][1]
        distances.append(vincenty(source[0], source[1], destination_lat, destination_lon))
    
    # print('check_1')
    return etas, distances

def distance_api(source, destinations):
    return osrm_api(source, destinations)