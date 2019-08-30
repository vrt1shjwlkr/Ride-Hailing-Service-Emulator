import csv, math

def perObfclassData(csv_file):
    total_num_rides = 0
    total_avg_obf_time_to_start_ride = 0
    total_avg_obf_num_of_trials = 0
    total_avg_real_time_to_start_ride = 0
    total_avg_real_num_of_trials = 0
    obf_class_prev = -1

    with open('per_obf_class_results.csv', 'w') as rf:
        rf_writer = csv.writer(rf)
        data = ['Obfuscation class', 'Number of rides', 'Obfuscated location avg time to start ride', 'Obfuscated location avg num of trial','Real location avg time to start ride', 'Real location avg num of trial','Difference']
        rf_writer.writerow(data)
        with open (csv_file, 'r') as cf:
            for i, line in enumerate(cf):
            	if line.startswith('last'):
            	    data = [obf_class_prev, total_num_rides, total_avg_obf_time_to_start_ride, total_avg_obf_num_of_trials, total_avg_real_time_to_start_ride, total_avg_real_num_of_trials, (total_avg_obf_time_to_start_ride - total_avg_real_time_to_start_ride)]
                    rf_writer.writerow(data)
                    break
                obf_class = int(line.split(',')[0])
                num_rides = int(line.split(',')[1])
                avg_obf_time_to_start_ride = float(line.split(',')[2])
                avg_obf_num_trials = float(line.split(',')[3])
                avg_real_time_to_start_ride = float(line.split(',')[4])
                avg_real_num_trials = float(line.split(',')[5])

                if obf_class == obf_class_prev:
                    total_avg_obf_time_to_start_ride = ((num_rides * avg_obf_time_to_start_ride) + (total_num_rides * total_avg_obf_time_to_start_ride))/(total_num_rides + num_rides)
                    total_avg_obf_num_of_trials = ((num_rides * avg_obf_num_trials) + (total_num_rides * total_avg_obf_num_of_trials))/(total_num_rides + num_rides)
                    total_avg_real_time_to_start_ride = ((num_rides * avg_real_time_to_start_ride) + (total_num_rides * total_avg_real_time_to_start_ride))/(total_num_rides + num_rides)
                    total_avg_real_num_of_trials = ((num_rides * avg_real_num_trials) + (total_num_rides * total_avg_real_num_of_trials))/(total_num_rides + num_rides)
                    total_num_rides = total_num_rides + num_rides
                else:
                    if obf_class_prev != -1 or obf_class_prev == 0:
                        # print to a csv file and then go to next class
                        data = [obf_class_prev, total_num_rides, total_avg_obf_time_to_start_ride, total_avg_obf_num_of_trials, total_avg_real_time_to_start_ride, total_avg_real_num_of_trials, (total_avg_obf_time_to_start_ride - total_avg_real_time_to_start_ride)]
                        rf_writer.writerow(data)
                        # initialize the variables
                        total_num_rides = 0
                        total_avg_obf_time_to_start_ride = 0
                        total_avg_real_time_to_start_ride = 0                        

                    total_num_rides = num_rides
                    total_avg_obf_time_to_start_ride = avg_obf_time_to_start_ride
                    total_avg_real_time_to_start_ride = avg_real_time_to_start_ride
                    total_avg_obf_num_of_trials = avg_obf_num_trials
                    total_avg_real_num_of_trials = avg_real_num_trials

                    obf_class_prev = obf_class

def calAverageTrials(csv_file):
    avg_trials = {}
    avg_real_trials = 0
    avg_obf_trials = 0
    with open(csv_file, 'r') as cf:
        for i, line in enumerate(cf,1):
            obf_class = math.floor(int(line.split(',')[9])/1000)
            obf_num_trials = int(line.split(',')[1])
            real_num_trials = int(line.split(',')[3])
            if obf_class in avg_trials.keys():
                num_rides = len(avg_trials[obf_class])
                avg_trials[obf_class] = [float((avg_trials[obf_class][0]*(num_rides) + obf_num_trials)/(num_rides + 1)), float((avg_trials[obf_class][1]*(num_rides) + real_num_trials)/(num_rides + 1)), avg_trials[obf_class][2] + 1]
            else:
                avg_trials[obf_class] = [obf_num_trials, real_num_trials, 1]
    
    with open('avg_trials1.csv', 'w') as af:
        af_writer = csv.writer(af)
        data = ['obf_class', 'Num of rides', 'avg obf trials', 'avg real trials']
        af_writer.writerow(data)
        for i in range(len(avg_trials)):
            data = [avg_trials.keys()[i], avg_trials[avg_trials.keys()[i]][2], avg_trials[avg_trials.keys()[i]][0], avg_trials[avg_trials.keys()[i]][1]]
            af_writer.writerow(data)

def perUserData(csv_file):
    total_num_rides = 0
    avg_obf_num_trials = 0
    avg_real_num_trials = 0
    avg_gen_util = 0
    avg_rhs_util = 0
    user_prev = -1
    
    with open('per_user_results.csv', 'w') as rf:
        rf_writer = csv.writer(rf)
        data = ['User', 'Number of rides', 'Avg Obf Trials', 'Avg Real Trials','Avg Gen Util', 'Avg RHS Util']
        rf_writer.writerow(data)
        with open(csv_file, 'r') as cf:
            for i, line in enumerate(cf, 1):
                if line.startswith('last'):
                    data = [user_prev, total_num_rides, avg_obf_num_trials, avg_real_num_trials, avg_gen_util, avg_rhs_util]
                    rf_writer.writerow(data)
                    break
                user = int(line.split(',')[0])
                obf_num_trials = float(line.split(',')[1])
                real_num_trials = float(line.split(',')[3])
                gen_util = float(line.split(',')[9])
                rhs_util = float(line.split(',')[10])
                if user == user_prev:
                    avg_obf_num_trials = ((obf_num_trials) + (total_num_rides * avg_obf_num_trials))/(total_num_rides + 1)
                    avg_real_num_trials = ((real_num_trials) + (total_num_rides * avg_real_num_trials))/(total_num_rides + 1)
                    avg_gen_util = (gen_util + (total_num_rides * avg_gen_util))/(total_num_rides + 1)
                    avg_rhs_util = (rhs_util + (total_num_rides * avg_rhs_util))/(total_num_rides + 1)
                    total_num_rides += 1
                else:
                    if user_prev != -1 or user_prev == 0:
                        # print to a csv file and then go to next class
                        data = [user_prev, total_num_rides, avg_obf_num_trials, avg_real_num_trials, avg_gen_util, avg_rhs_util]
                        rf_writer.writerow(data)
                        # initialize the variables
                        total_num_rides = 0
                        avg_obf_num_trials = 0
                        avg_real_num_trials = 0
                        avg_gen_util = 0
                        avg_rhs_util = 0

                    avg_obf_num_trials = obf_num_trials
                    avg_real_num_trials = real_num_trials
                    avg_gen_util = gen_util
                    avg_rhs_util = rhs_util
                    total_num_rides = 1
                    user_prev = user

# perUserData('test.csv')
# perObfclassData('test.csv')
# calAverageTrials('test2.csv')