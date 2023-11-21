import datetime
from datetime import timedelta
import time
import subprocess
from fabric import Connection
import paramiko
import math
from scipy import stats
import pandas as pd
import numpy as np
import os
import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")
from dateutil.parser import parse
from analysis.endtime_none_tek_net import coding_process, power_measurement, run_parallel_processes, stop_remote_process, powerlog_copy
from functools import partial
from analysis.task_energy import calc_energies_on_dataframe, calc_job_energy_on_job_row, calc_job_energy_on_job_row_single


def test_calc_job_energy(count_encode, encode_power, encode_time):
    start_encode = encode_time[0]
    end_encode = encode_time[-1]

    count = count_encode
    if count == 1:
        df = pd.DataFrame(
            data={
                'target_encode': [{'start_time': start_encode, 'end_time': end_encode}]
            },
            dtype=object
        )
        dti_e = pd.to_datetime(encode_time)
        power_encode_list = encode_power
        df_power_e = pd.Series(data=power_encode_list, name='power', index=dti_e)
        # print(df_power_e)
        _calc_job_energy_target_encode = partial(calc_job_energy_on_job_row_single, df_power_e,
                                                 lambda x: x['target_encode']['start_time'],
                                                 lambda x: x['target_encode']['end_time'])
        df['target_encode_energy'] = df.apply(_calc_job_energy_target_encode, axis=1)

    else:
        df = pd.DataFrame(
            data={
                  'start_time_encode': [start_encode], 'end_time_encode': [end_encode], 'count_encode': [count]
                  },
            dtype=object
        )
        dti_e = pd.to_datetime(encode_time)
        power_encode_list = encode_power
        df_power_e = pd.Series(data=power_encode_list, name='power', index=dti_e)
        # print(df_power_e)
        _calc_job_energy_encode = partial(calc_job_energy_on_job_row, df_power_e,
                                          lambda x: x[f'start_time_encode'],
                                          lambda x: x[f'end_time_encode'],
                                          lambda x: x[f'count_encode'])
        df['target_encode_energy'] = df.apply(_calc_job_energy_encode, axis=1)

    return df

def get_power_data(cmd):
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key
    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    print("code sleep 5 secs")
    time.sleep(5)
    run_parallel_processes(cmd)
    stop_remote_process(conn, 'python')
    power_log = powerlog_copy(conn)
    print("code sleep 5 secs")
    time.sleep(5)

    return power_log

def get_power_list(power_log):
    time_list = power_log['time_stamp'].tolist()
    power_list = power_log['power'].tolist()
    return power_list, time_list

def meets_condition1_poweridle(power_list):
    power_array = np.array(power_list)

    # Average idle power
    power_idle = 80
    # Threshold value
    threshold = 1.05
    average_power = sum(power_array) / len(power_array)

    return average_power > power_idle * threshold

def meets_condition2_tdistribution(power_list):
    flat_list = [item for sublist in power_list for item in sublist]
    power_array = np.array(flat_list)

    alpha = 0.05
    n = len(power_array)  # Sample size
    sample_std = np.std(power_array, ddof=1)
    sample_mean = np.mean(power_array)
    t_alpha_half = stats.t.ppf(1 - alpha / 2, df=n - 1)

    left_side = (t_alpha_half * sample_std) / (2 * alpha * sample_mean)
    right_side = n * math.sqrt(2 * n)
    # If the criteria are met, return True; otherwise, return False
    print(f'left_side of the equation:{left_side}')
    print(f'right side of the equation: {right_side}')
    return left_side < right_side, left_side, right_side


def measure_command_runtime_distribution(cmd):
    count_encode = 0
    encoding_processes = {}
    consecutive_failures = 0
    total_power_list = []

    while True:

        power_log = get_power_data(cmd)
        current_power_list, time_list = get_power_list(power_log) #current power

        if meets_condition1_poweridle(current_power_list):
            print('Satisfying condition 1: idle power check')
            total_power_list.append(current_power_list)
            count_encode += 1
            encoding_processes[count_encode] = (current_power_list, time_list)
            consecutive_failures = 0

            # put a logging (keep the measurement of formula inequality sides)
            measure, left_side, right_side = meets_condition2_tdistribution(total_power_list)
            if measure:
                print('Satisfying condition 2: t-distribution')
                break
            elif count_encode > 100:
                print('Timed out')
                break  # count_encode >100 we break the loop #take the logging notes
        else:
            consecutive_failures += 1

        if consecutive_failures >= 5:
            break

    return encoding_processes


if __name__ == '__main__':
    codec = 'SVT-AV1'

    if codec == 'SVT-AV1':
        codec_name = 'libsvtav1'  # 'libaom-av1' #'libsvtav1'
        # qp_level = [12]
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]

    df_metrics = pd.DataFrame(columns=['vid', 'QP', 'start_time_encode', 'end_time_encode', 'count_encode', 'target_encode_energy'])

    vid_list = []
    qp_list = []
    count_encode_list = []
    start_time_encode_list = []
    end_time_encode_list = []
    encode_energy_list = []

    for qp in qp_level:
        vid_list.append('Animation_1080P-3d67')
        qp_list.append(qp)

        encode_command = f'ffmpeg -s 1920x1080 -r 25.0 -pix_fmt yuv420p -y -i ../videocodec/input/Animation_1080P-3d67.yuv -c:v libsvtav1 -cpu-used 0 -crf {str(qp)} ../videocodec/encoded/SVT-AV1/Animation_1080P-3d67_encoded_fps25.0_crf_{str(qp)}.mp4 1>../videocodec/encoded/SVT-AV1/encoded_test_log_crf_{str(qp)}.txt 2>&1'
        encoding_processes = measure_command_runtime_distribution(encode_command)
        print("code sleep 10 secs")
        time.sleep(10)

        count_encode = len(encoding_processes)
        # print(encoding_processes)
        # print(f'count_encode: {count_encode}')
        # df_power = pd.DataFrame.from_dict(encoding_processes, orient='index', columns=['power', 'time_stamp'])
        # print(df_power)

        print("==================================================================")
        df_power = []
        for key, value in encoding_processes.items():
            df = pd.DataFrame({'power': value[0], 'time_stamp': value[1]})
            df_power.append(df)
        merged_df_power = pd.concat(df_power, ignore_index=True)
        print(merged_df_power)
        print("==================================================================")
        encode_power, encode_time = get_power_list(merged_df_power)
        df_energy = test_calc_job_energy(count_encode, encode_power, encode_time)
        print(df_energy.T)
        print("==================================================================")

        start_time = merged_df_power.iloc[0]['time_stamp']
        end_time = merged_df_power.iloc[-1]['time_stamp']

        # print(f'start_time: {start_time}')
        # print(f'end_time: {end_time}')
        count_encode_list.append(count_encode)
        start_time_encode_list.append(start_time)
        end_time_encode_list.append(end_time)
        encode_energy_list.append(df_energy['target_encode_energy'][0])

        os.remove(f'../videocodec/encoded/SVT-AV1/TelevisionClip_1080P-68c6_encoded_fps25.0_crf_{str(qp)}.mp4')
        os.remove('../metrics/energy_log/power_log.csv')

    df_metrics['vid'] = vid_list
    df_metrics['QP'] = qp_list
    df_metrics['count_encode'] = count_encode_list
    df_metrics['start_time_encode'] = start_time_encode_list
    df_metrics['end_time_encode'] = end_time_encode_list
    df_metrics['target_encode_energy'] = encode_energy_list

    print(df_metrics)
    metrics_name = f'../metrics/energy_log/YOUTUBE_UGC_1080P_{codec}_distribution_energy_test.csv'
    df_metrics.to_csv(metrics_name, index=None)