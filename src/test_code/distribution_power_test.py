import datetime
import subprocess
from fabric import Connection
import pandas as pd
import paramiko
import math
from scipy import stats
import numpy as np
import os
import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

def copy_file():
    # Perform the file copying from one server to another
    print("Copying file from server power to server videoenc...")

    # do_fabric():
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key

    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)

    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    # Download a file from the remote host to the local host
    print('-----------get power_log file-----------')
    remote_path = '/home/pi/tek_power/power_log_2023-05-15.csv'
    local_path = '/home/um20242/quality-energy/metrics/energy_log/'
    logfile_name = f'{local_path}power_log_2023-05-15.csv'

    conn.get(remote=remote_path, local=local_path)
    power_log = pd.read_csv(logfile_name, names=['time_stamp', 'power'])
    power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])
    # print(power_log.head())
    
    # Close the connection
    conn.close()

    # Check if the file exists
    if os.path.exists(logfile_name):
        os.remove(logfile_name) # remove power log file
    else:
        print(f'The file {logfile_name} does not exist.')

    return power_log

def get_nearest_power(start_time, end_time):
    # Copy the file from the server to another server
    power_log = copy_file()
    power_log = power_log.set_index('time_stamp')  # Set date to index

    index_start = power_log.index.get_indexer([start_time], method='nearest')[0] #new version
    index_end = power_log.index.get_indexer([end_time], method='nearest')[0]

    print(start_time)
    print(end_time)
    
    power_log = power_log.reset_index()
    power_select = power_log.loc[index_start:index_end, ['time_stamp', 'power']]#one到two行，ac列
    print(power_select)
    time_list = power_select['time_stamp'].tolist()
    power_list = power_select['power'].tolist()

    return power_list, time_list

def meets_criteria(start_time_encode, end_time_encode):

    power_list, time_list = get_nearest_power(start_time_encode, end_time_encode)

    alpha = 0.05
    satisfy_condition = one_sample_t_test(power_list, alpha)

    # If the criteria are met, return True; otherwise, return False
    return satisfy_condition

def one_sample_t_test(data, alpha):
    # Calculate sample information
    n = len(data)  # Sample size
    sample_mean = np.mean(data)  # Sample mean
    sample_std = np.std(data, ddof=1)  # Sample standard deviation, ddof=1 for small samples

    # Calculate t_alpha/2
    t_alpha_half = stats.t.ppf(1 - alpha/2, df=n-1)
    print(t_alpha_half)

    # Calculate the right side of the equation
    left_side= (t_alpha_half * sample_std) / (2 * alpha * sample_mean)
    print(f'left_side: {left_side}')

    # Calculate the left side of the equation
    right_side = n * math.sqrt(2 * n)
    print(f'right_side: {right_side}')

    # Check if the equation condition is satisfied
    satisfy_condition = left_side < right_side
    print(satisfy_condition)

    return satisfy_condition

def measure_command_runtime_distribution(cmd):
    print(f'running ffmpeg with command:')
    count_repeat = 10  # 1 time for just considering the encoding time first
    start_time = datetime.datetime.now()

    for i in range(count_repeat):
        print(str(i + 1) + ' times: ' + cmd)
        start_time_encode = datetime.datetime.now()
        subprocess.run(cmd, encoding="utf-8", shell=True)
        end_time_encode = datetime.datetime.now()

        # Calculate the measurement: Calculate the formula and check if it meets the criteria
        if meets_criteria(start_time_encode, end_time_encode):
            end_time = datetime.datetime.now()
            count_encode = i + 1
            break  # Stop the repeat encoding process if criteria are met

        else:
            end_time = datetime.datetime.now()
            count_encode = i + 1
            
        print('------------------------------------------------------------------------------')

    return start_time, end_time, count_encode

# Example usage
if __name__ == '__main__':
    codec = 'SVT-AV1'

    if codec == 'SVT-AV1':
        codec_name = 'libsvtav1'  # 'libaom-av1' #'libsvtav1'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]

    df_metrics = pd.DataFrame(columns=['vid', 'QP', 'start_time_encode', 'end_time_encode', 'count_encode'])

    vid_list = []
    qp_list = []
    count_encode_list = []
    start_time_encode_list = []
    end_time_encode_list = []

    for qp in qp_level:
        vid_list.append('TelevisionClip_1080P-68c6')
        qp_list.append(qp)

        encode_command = f'ffmpeg -s 1920x1080 -r 25.0 -pix_fmt yuv420p -y -i ../videocodec/input/TelevisionClip_1080P-68c6.yuv -c:v libsvtav1 -crf {str(qp)} ../videocodec/encoded/SVT-AV1/TelevisionClip_1080P-68c6_encoded_fps25.0_crf_{str(qp)}.mp4 1>../videocodec/encoded/SVT-AV1/encoded_test_log_crf_{str(qp)}.txt 2>&1'
        start_time, end_time, count_encode = measure_command_runtime_distribution(encode_command)

        print(f'start_time: {start_time}')
        print(f'end_time: {end_time}')
        print(f'count_encode: {count_encode}')

        count_encode_list.append(count_encode)
        start_time_encode_list.append(start_time)
        end_time_encode_list.append(end_time)

    df_metrics['vid'] = vid_list
    df_metrics['QP'] = qp_list
    df_metrics['count_encode'] = count_encode_list
    df_metrics['start_time_encode'] = start_time_encode_list
    df_metrics['end_time_encode'] = end_time_encode_list

    print(df_metrics)
    metrics_name = f'../metrics/energy_log/YOUTUBE_UGC_1080P_{codec}_distribution_test.csv'
    df_metrics.to_csv(metrics_name, index=None)