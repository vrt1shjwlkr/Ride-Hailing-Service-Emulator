from __future__ import division
import simpy, os, datetime, random, simplejson, urllib, csv, sys, collections, math, logging, numpy
from pathlib import Path

'''
This function will aggregate the utility parameters of drivers
'''

def driverUtilCSV(server, foldername, filename, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, generic_util, mech_name):
    file_name = foldername+ '/consolidated_d_' + mech_name + '_' + dd_surge_neg + '_' + dd_surge_less_than_one + '_' + dd_surge_more_than_one + '_' + str(server.driverObjects[0].tolerance) + '_' + str(server.riderObjects[0].req_delay) + '.csv'
    drivers = server.driverObjects
    avg_rhs_util_d = []
    avg_real_acc = []
    avg_obf_acc = []
    avg_real_acc_rides = []
    avg_obf_acc_rides = []
    avg_real_earning = []
    avg_obf_earning = []
    consolidated_csv =[]
    consolidated_header = ['Obfuscation class', 'avg_real_acc_rate', 'avg_real_accepted_rides', 'avg_real_earnings', 'std_real_earnings', 'avg_obf_acc_rate', 'avg_obf_accepted_rides', 'avg_obf_earnings', 'std_obf_earnings', 'rhs_util_d']

    with open(filename, 'w') as rf:
        rf_writer = csv.writer(rf)
        data = ['Driver ID', 'real_acc_rate', 'real_earnings', 'Real accepted rides', 'obf_acc_rate', 'obf_earnings', 'Obf accepted rides', 'Drivers RHS Util']
        rf_writer.writerow(data)
        for i in range(len(drivers)):
            real_money = sum(drivers[i].real_earnings)
            obf_money = sum(drivers[i].obf_earnings)
            rhs_util_d = real_money - obf_money
            avg_rhs_util_d.append(rhs_util_d)
            real_acc = drivers[i].real_acc_rate if drivers[i].real_acc_rate else 0
            avg_real_acc.append(real_acc)
            avg_real_acc_rides.append(drivers[i].real_acc_rides)
            obf_acc = drivers[i].obf_acc_rate if drivers[i].obf_acc_rate else 0
            avg_obf_acc.append(obf_acc)
            avg_obf_acc_rides.append(drivers[i].obf_acc_rides)
            avg_real_earning.append(real_money)
            avg_obf_earning.append(obf_money)

            if drivers[i].real_acc_rides == 0 and drivers[i].obf_acc_rides == 0:
                continue
            data = [drivers[i].id, drivers[i].real_acc_rate, real_money, drivers[i].real_acc_rides, drivers[i].obf_acc_rate, obf_money, drivers[i].obf_acc_rides, rhs_util_d]
            rf_writer.writerow(data)

        obf_amount = generic_util * 1000
        avg_real_acc_r = sum(avg_real_acc)/len(avg_real_acc)
        avg_real_e = sum(avg_real_earning)/len(avg_real_earning)
        std_real_e = numpy.std(avg_real_earning)
        avg_obf_acc_r = sum(avg_obf_acc)/len(avg_obf_acc)
        avg_obf_e = sum(avg_obf_earning)/len(avg_obf_earning)
        std_obf_e = numpy.std(avg_obf_earning)
        real_avg_acc_rides = sum(avg_real_acc_rides)/len(avg_real_acc_rides)
        obf_avg_acc_rides = sum(avg_obf_acc_rides)/len(avg_obf_acc_rides)
        consolidated_data = [obf_amount, avg_real_acc_r, real_avg_acc_rides, avg_real_e, std_real_e, avg_obf_acc_r, obf_avg_acc_rides, avg_obf_e, std_obf_e, (avg_real_e - avg_obf_e)]
        consolidated_file = Path('./' +file_name)
        if consolidated_file.is_file():
            pass
        else:
            cr = open(file_name, 'w')
            cr_writer = csv.writer(cr)
            cr_writer.writerow(consolidated_header)
            cr.close()

        with open(file_name, 'r') as cr:
            cr_reader = csv.reader(cr)
            for row in cr_reader:
                consolidated_csv.append(row)
            cr.close()
        consolidated_csv.pop(0)
        row_found = False
        for i in range(len(consolidated_csv)):
            if float(consolidated_csv[i][0]) == obf_amount:
                row_found = True
                consolidated_csv[i] = consolidated_data
            else:
                pass

        if row_found:
            pass
        else:
            consolidated_csv.append(consolidated_data)

        with open(file_name, 'w') as cr:
            cr_writer = csv.writer(cr)
            cr_writer.writerow(consolidated_header)
            for i in range(len(consolidated_csv)):
                cr_writer.writerow(consolidated_csv[i])
        cr.close()

'''
This file contains functions which generate and write relevant ride details to a csv file
'''
def generateCSV(server, foldername, filename, obf_class_size, num_riders, num_drivers, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, mech_name, count, gen_utility):
    avg_results = {}
    total_rides = 0
    obf_amount = None
    obfuscation_class = None
    obf_class = None
    privacy_level = None
    consolidated_csv = []

    with open(filename, 'w') as rf:
        rf_writer = csv.writer(rf)
        data = ['Rider ID', 'obfuscated_trials', 'obfuscated_extras', 'real_trials', 'obf_ride_complete', 'real_ride_complete', 'ride_request_time', 'obf_time_to_accept', 'obf_loc time to start ride', 'real_time_to_accept', 'real_loc time to start ride', 'generic_util', 'RHS_util', 'real_loc num drivers', 'real_loc avg_driver_dist', 'real_acc_rate', 'real_loc surge', 'obf_loc num drivers', 'obf_loc avg_driver_dist', 'obf_acc_rate', 'obf_loc surge', 'obf-real ETA', 'Privacy Level', 'Avg min real ETA', 'Avg min obf ETA', 'Real accept eta_tolerance', 'Obf accept eta_tolerance', 'Real accept_eta', 'Obf accept_eta', 'Euclidean QL', 'Expected Gen QL', 'Expected Tai QL']
        rf_writer.writerow(data)
        privacy_level = server.riderObjects[0].privacy_level
        for i in range(num_riders):
            if server.riderObjects[i].rideDetails:
                total_rides += len(server.riderObjects[i].rideDetails)
                for j in range(len(server.riderObjects[i].rideDetails)):
                    temp = server.riderObjects[i].rideDetails[j]
                    # print(temp)
                    obf_amount = temp[10]
                    data = [server.riderObjects[i].id, temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8], temp[9], temp[10], (temp[7] - temp[9]), temp[12]/temp[2], temp[13]/temp[12], temp[14]/temp[12], temp[15]/temp[2], temp[16]/temp[0], temp[17]/temp[16], temp[18]/temp[16], temp[19]/temp[0], temp[20], temp[21], temp[22]/temp[2], temp[23]/temp[0], temp[24], temp[25], temp[26], temp[27], temp[28], temp[29], temp[30]]
                    obf_class = math.floor(temp[10]/obf_class_size)
                    # For totally complete rides, define an obfuscation level for each generic utility
                    if obf_class in avg_results.keys():
                        temp1 = avg_results[obf_class][7]
                        temp1.append(temp[7] - temp[9])
                        
                        temp2 = avg_results[obf_class][8]
                        temp2.append(temp[20])
                        
                        temp3 = avg_results[obf_class][9]
                        temp3.append(temp[28])

                        temp4 = avg_results[obf_class][10]
                        temp4.append(temp[29])

                        temp5 = avg_results[obf_class][11]
                        temp5.append(temp[30])

                        avg_results[obf_class] = [avg_results[obf_class][0] + temp[7], avg_results[obf_class][1] + temp[9], avg_results[obf_class][2] + temp[0], avg_results[obf_class][3] + temp[2], avg_results[obf_class][4] + 1, avg_results[obf_class][5] + abs(temp[3]-1), avg_results[obf_class][6] + abs(temp[4]-1), temp1, temp2, temp3, temp4, temp5]
                    else:
                        avg_results[obf_class] = [temp[7], temp[9], temp[0], temp[2], 1, abs(temp[3]-1), abs(temp[4]-1), [(temp[7] - temp[9])], [temp[20]], [temp[28]], [temp[29]], [temp[30]]]
                    rf_writer.writerow(data)

        space = ['\n\n']
        rf_writer.writerow(space)

        ordered_results = collections.OrderedDict(sorted(avg_results.items()))
        consolidated_header = ['count','Obfuscation class', 'Number of rides', 'Incomplete Obf Rides', 'Incomplete Real Rides', 'Obfuscated location avg time to start ride', 'Obfuscated location avg num of trials','Real location avg time to start ride', 'Real location avg num of trials', 'avg rhs util', 'avg diff trials', 'StD RHS util', 'Avg Obf-Real ETA', 'Privacy level', 'ST Deviation real-obf distance', 'Avg Euclidean QL', 'Std Euclidean QL', 'Avg Exp Euclidean QL', 'Std Exp Euclidean QL', 'Avg Exp Tailored QL', 'Std Exp Tailored QL']

        for i in range(len(ordered_results)):
            obfuscation_class = list(ordered_results.keys())[i]
            num_rides = ordered_results[obfuscation_class][4]
            avg_obf_time_to_start_ride = ordered_results[obfuscation_class][0]/num_rides
            avg_real_time_to_start_ride = ordered_results[obfuscation_class][1]/num_rides
            avg_obf_num_of_trials = ordered_results[obfuscation_class][2]/num_rides
            avg_real_num_of_trials = ordered_results[obfuscation_class][3]/num_rides
            obf_incomplete_rides = ordered_results[obfuscation_class][5]
            real_incomplete_rides = ordered_results[obfuscation_class][6]
            std_rhs = numpy.std(ordered_results[obfuscation_class][7])
            
            avg_obf_dist = numpy.sum(ordered_results[obfuscation_class][8])/num_rides
            std_obf_dist = numpy.std(ordered_results[obfuscation_class][8])
            
            avg_euclidean_dist = numpy.sum(ordered_results[obfuscation_class][9])/num_rides
            std_euclidean_dist = numpy.std(ordered_results[obfuscation_class][9])
            
            avg_gen_ql=numpy.sum(ordered_results[obfuscation_class][10])/num_rides
            std_gen_ql=numpy.std(ordered_results[obfuscation_class][10])

            avg_tai_ql=numpy.sum(ordered_results[obfuscation_class][11])/num_rides
            std_tai_ql=numpy.std(ordered_results[obfuscation_class][11])

            consolidated_data = [count, obf_amount, num_rides, obf_incomplete_rides, real_incomplete_rides, avg_obf_time_to_start_ride, avg_obf_num_of_trials, avg_real_time_to_start_ride, avg_real_num_of_trials, (avg_obf_time_to_start_ride - avg_real_time_to_start_ride), (avg_obf_num_of_trials - avg_real_num_of_trials), std_rhs, avg_obf_dist, privacy_level, std_obf_dist, avg_euclidean_dist, std_euclidean_dist, avg_gen_ql, std_gen_ql, avg_tai_ql, std_tai_ql]

            filename = foldername + '/consolidated_' + mech_name + '_' + dd_surge_neg + '_' + dd_surge_less_than_one + '_' + dd_surge_more_than_one + '_' + str(server.driverObjects[0].tolerance) + '_' + str(server.riderObjects[0].req_delay) + '_' +str(gen_utility) + '.csv'
            consolidated_file = Path('./' +filename)
            if consolidated_file.is_file():
                pass
            else:
                # Create a file and write header to it
                cr = open(filename, 'w')
                cr_writer = csv.writer(cr)
                cr_writer.writerow(consolidated_header)
                cr.close()

            with open(filename, 'r') as cr:
                cr_reader = csv.reader(cr)
                for row in cr_reader:
                    consolidated_csv.append(row)
                cr.close()
            consolidated_csv.pop(0)

            row_found = False
            for i in range(len(consolidated_csv)):
                if float(consolidated_csv[i][0])==count and float(consolidated_csv[i][1])==obf_amount and float(consolidated_csv[i][13]) == privacy_level:
                    row_found = True
                    consolidated_csv[i] = consolidated_data
                else:
                    pass

            if row_found:
                pass
            else:
                consolidated_csv.append(consolidated_data)

            with open(filename, 'w') as cr:
                cr_writer = csv.writer(cr)
                cr_writer.writerow(consolidated_header)
                for i in range(len(consolidated_csv)):
                    cr_writer.writerow(consolidated_csv[i])
            cr.close()

decision_model_dict = {'hard':0, 'exp':1, 'log':2, 'lin':3}
def generate_regression_data(server, num_riders, num_drivers, regression_data_file, eta_tolerance, mech_number, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one):
    regression_f = open(regression_data_file, 'a')
    regression_writer = csv.writer(regression_f)
    # regression_header = ['Obfuscation Mechanism', 'driver decision model', 'driver dist tolerance', 'Riders/Drivers', 'obfuscation level', 'Obf-Real ETA', 'Real Num of drivers', 'Real Avg distances of drivers', 'Real Avg acceptance rate', 'Real Surge factor', 'Obf Num of drivers', 'Obf Avg distances of drivers', 'Obf Avg acceptance rate', 'Obf Surge factor', 'RHS Util']
    for i in range(num_riders):
        if server.riderObjects[i].rideDetails:
            for j in range(len(server.riderObjects[i].rideDetails)):
                temp = server.riderObjects[i].rideDetails[j]
                regression_data = [mech_number, eta_tolerance, (num_riders/num_drivers), server.riderObjects[i].gen_utility, temp[20], temp[12]/temp[2], temp[13]/temp[12], temp[14]/temp[12], temp[15]/temp[2], temp[16]/temp[0], temp[17]/temp[16], temp[18]/temp[16], temp[19]/temp[0], (temp[7] - temp[9]), temp[21], decision_model_dict.get(dd_surge_neg), decision_model_dict.get(dd_surge_less_than_one), decision_model_dict.get(dd_surge_more_than_one), temp[2], temp[0], temp[1], temp[3], temp[4], temp[22]/temp[2], temp[23]/temp[0], temp[24], temp[25], temp[26], temp[27], temp[28]]
                regression_writer.writerow(regression_data)
    regression_f.close()

def d_generate_regression_data(server, num_riders, num_drivers, d_regression_data_file, eta_tolerance, mech_number, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one):
    d_regression_f = open(d_regression_data_file, 'a')
    d_regression_writer = csv.writer(d_regression_f)
    drivers = server.driverObjects
    # d_regression_header = ['Obfuscation Mechanism', 'driver dist tolerance', 'Riders/Drivers', 'obfuscation level', 'Obf earnings', 'Real earning', RHS util', 'SF neg', 'SF less_than_one', 'SF more_than_one', 'Real accepted rides', 'Obf accepted rides']
    for driver in drivers:
        if driver.real_acc_rides == 0 and driver.obf_acc_rides == 0:
            continue
        regression_data = [mech_number, eta_tolerance, (num_riders/num_drivers), driver.gen_utility, sum(driver.obf_earnings), sum(driver.real_earnings), (sum(driver.real_earnings) - sum(driver.obf_earnings)), decision_model_dict.get(dd_surge_neg), decision_model_dict.get(dd_surge_less_than_one), decision_model_dict.get(dd_surge_more_than_one), driver.real_acc_rides, driver.obf_acc_rides]
        d_regression_writer.writerow(regression_data)
    d_regression_f.close()