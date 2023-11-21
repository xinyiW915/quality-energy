import datetime
from datetime import timedelta
import time
import os

import pandas as pd
import numpy as np
from scipy import stats
import math

def get_power_list(power_log):
    time_list = power_log['time_stamp'].tolist()
    power_list = power_log['power'].tolist()
    return power_list, time_list

def meets_condition1_poweridle(power_list):
    # Average idle power
    power_idle = 78
    # Threshold value
    threshold = 1.05
    power_array = np.array(power_list)

    if len(power_array) != 0:
        average_power = sum(power_array) / len(power_array)
        print(f'total average power: {average_power}')
        condition1 = average_power > power_idle * threshold

        if condition1:
            window_size = 3  # Size of the moving window
            num_below_threshold = 0  # Counter for moving average below threshold

            if len(power_array) >= window_size:
                for i in range(len(power_array) - window_size + 1):
                    window = power_array[i:i + window_size]
                    moving_average = np.mean(window)
                    print(f'moving average: {moving_average}')
                    if moving_average < power_idle * threshold:
                        num_below_threshold += 1
                        if num_below_threshold >= 3:
                            print(f'More than 3 times the moving average < idel power * threshold  \n')
                            return False  # break if condition2 is not met

            return True  # If we reach here, both conditions are met
        else:
            print(f'total average power < idel power * threshold')
            return False  # If condition1 is not met, return False
    else:
        print('Power list is empty')
        return False

def meets_condition2_tdistribution(power_list):
    flat_list = [item for sublist in power_list for item in sublist]
    power_array = np.array(flat_list)
    print(f'power_array: {power_array}')
    if len(power_array) != 0:
        alpha = 0.05
        n = len(power_array)  # Sample size
        sample_std = np.std(power_array, ddof=1)
        sample_mean = np.mean(power_array)
        t_alpha_half = stats.t.ppf(1 - alpha / 2, df=n - 1)

        left_side = (t_alpha_half * sample_std) / (2 * alpha * sample_mean)
        right_side = n * math.sqrt(2 * n)
        condition2 = left_side < right_side
        # If the criteria are met, return True; otherwise, return False
        print(f'left_side of the equation:{left_side}')
        print((f'right side of the equation: {right_side}'))
    else:
        print('Power list is empty')
        condition2 = False
        left_side = None
        right_side = None
        print(f'left_side of the equation:{left_side}')
        print((f'right side of the equation: {right_side}'))

    return condition2, left_side, right_side

def list2array(power_list):
    flat_list = [item for sublist in power_list for item in sublist]
    power_array = np.array(flat_list)
    return power_array

# failure example:
current_power_list = [95,100,80,80,70,70,70]
current_time_list = [95,100,80,80,70,70,70]
# current_time_list = [pd.Timestamp('2023-09-29 18:31:48.580000'), pd.Timestamp('2023-09-29 18:31:49.421000'), pd.Timestamp('2023-09-29 18:31:50.299000')]

# meet condition1 example:
# current_power_list = [88.725, 78.883, 200.2]
# current_time_list = [pd.Timestamp('2023-09-29 18:31:48.580000'), pd.Timestamp('2023-09-29 18:31:49.421000'), pd.Timestamp('2023-09-29 18:31:50.299000')]

# meet condition2 example:
# current_power_list = [205.5, 206.63, 208.13]
# current_time_list = [pd.Timestamp('2023-09-29 18:31:48.580000'), pd.Timestamp('2023-09-29 18:31:49.421000'), pd.Timestamp('2023-09-29 18:31:50.299000')]

count_repeat = 0
coding_processes = {}
consecutive_failures = 0

total_power_list = []
total_time_list = []
total_power_log = pd.DataFrame(columns=['time_stamp', 'power'])

failure_power_list = []
failure_time_list = []

def extract_power_list2meet_tdistributions(data):
    result = []
    for key, value in data.items():
        first_list = value[0]
        result.extend(first_list)

    power_array = np.array(result)
    print(f'power_array: {power_array}')
    if len(power_array) != 0:
        alpha = 0.05
        n = len(power_array)  # Sample size
        sample_std = np.std(power_array, ddof=1)
        sample_mean = np.mean(power_array)
        t_alpha_half = stats.t.ppf(1 - alpha / 2, df=n - 1)

        left_side = (t_alpha_half * sample_std) / (2 * alpha * sample_mean)
        right_side = n * math.sqrt(2 * n)
        condition = left_side < right_side
        # If the criteria are met, return True; otherwise, return False
        print(f'left_side of the equation:{left_side}')
        print((f'right side of the equation: {right_side}'))
    return condition

def measure_command_runtime_distribution(cmd, repeat_time, old_video_path, test_power, test_time):
    print(f'running ffmpeg with command: {cmd}')

    count_repeat = 0
    coding_processes = {}
    consecutive_failures = 0

    total_power_list = []
    total_time_list = []
    total_power_log = pd.DataFrame(columns=['time_stamp', 'power'])

    failure_power_list = []
    failure_time_list = []

    for i in range(repeat_time):
        # Check if we already found a satisfying coding process

        if coding_processes:
            check_power_list = extract_power_list2meet_tdistributions(coding_processes)
            print(f'check_power_list: {check_power_list}')
            if measure:
                print("Existing coding process found. Exiting the loop.")
                break

        # if i != 0:
        #     os.remove(old_video_path)

        print("==================================================================")
        print(str(i + 1) + ' times')
        tmp_power_list = []

        while True:
            # power_log = get_power_data(cmd)
            power_log = pd.DataFrame({'power': test_power, 'time_stamp': test_time})
            current_power_list, current_time_list = get_power_list(power_log)  # current power
            print(f'current_power_list: {current_power_list}')

            total_power_log = pd.concat([total_power_log, power_log])
            # print(f'total_power_log: {total_power_log}')

            if meets_condition1_poweridle(current_power_list):
                print('Satisfying condition 1: idle power check')
                count_repeat += 1
                total_power_list.append(current_power_list)
                total_time_list.append(current_time_list)
                coding_processes[count_repeat] = (current_power_list, current_time_list)

                tmp_power_list.append(current_power_list)

                # Check the distribution condition
                measure, left_side, right_side = meets_condition2_tdistribution(tmp_power_list)
                if measure:
                    print('Satisfying condition 2: t-distribution')
                    break
                elif count_repeat > 100:
                    print('Timed out, count_repeat > 100')
                    break
                else:
                    print('Not satisfying condition 2: t-distribution. Retrying...\n')
            else:
                consecutive_failures += 1
                print(f'consecutive_failures: {consecutive_failures}')
                failure_power_list.append(current_power_list)
                failure_time_list.append(current_time_list)

            if consecutive_failures >= 5:
                print(f'consecutive_failures: {consecutive_failures}')
                break

    return coding_processes, total_power_list, total_time_list, failure_power_list, failure_time_list

cmd = 'ffmpeg----'
repeat_time = 10
old_video_path = 'old video path'

coding_processes, total_power_list, total_time_list, failure_power_list, failure_time_list = measure_command_runtime_distribution(cmd, repeat_time, old_video_path, current_power_list, current_time_list)
print("\n -----------------------------------------------------------------")
print(total_power_list)

while not coding_processes:
    current_power_list = [88.725, 78.883, 200.2]
    current_time_list = [pd.Timestamp('2023-09-29 18:31:48.580000'), pd.Timestamp('2023-09-29 18:31:49.421000'), pd.Timestamp('2023-09-29 18:31:50.299000')]
    coding_processes, total_power_list, total_time_list, failure_power_list, failure_time_list = measure_command_runtime_distribution(cmd, repeat_time, old_video_path, current_power_list, current_time_list)

print("-----------------------------------------------------------------")
print(coding_processes)
print(len(coding_processes))
print(total_power_list)
print(len(total_power_list))
print(failure_power_list)
print(len(failure_power_list))
print("-----------------------------------------------------------------")


def test_calc_job_energy(coding_power, coding_time):
    start_coding = coding_time[0]
    end_coding = coding_time[-1]

    df = pd.DataFrame(
        data={
            'target_coding': [{'start_time': start_coding, 'end_time': end_coding}]
        },
        dtype=object
    )
    dti_e = pd.to_datetime(coding_time)
    power_coding_list = coding_power
    df_power_e = pd.Series(data=power_coding_list, name='power', index=dti_e)

    # _calc_job_energy_target_coding = partial(calc_job_energy_on_job_row_single, df_power_e,
    #                                          lambda x: x['target_coding']['start_time'],
    #                                          lambda x: x['target_coding']['end_time'])
    # df['target_coding_energy'] = df.apply(_calc_job_energy_target_coding, axis=1)
    df['target_coding_energy'] = np.mean(power_coding_list)

    return df

def cal_energy_log(coding_processes, duplicate_count):
    print(f'coding_processes: {coding_processes}')
    count_coding = len(coding_processes)
    print(f'count_repeat: {count_coding}')
    print("==================================================================")

    if count_coding == 0:
        print(f'No successful coding process')
        start_time = None
        end_time = None
        coding_energy = None

    else:
        df_power = []
        coding_energy_list = []
        repeat_count = 0

        for key, value in coding_processes.items():
            df = pd.DataFrame({'power': value[0], 'time_stamp': value[1]})
            coding_power, coding_time = get_power_list(df)

            repeat_count += 1
            print(str(repeat_count) + ' times')
            print(f'coding_power: {coding_power}')
            print(f'coding_time: {coding_time}')

            df_energy = test_calc_job_energy(coding_power, coding_time)
            print(f'df_energy: {df_energy.T}')
            print("==================================================================")
            target_coding_energy = df_energy['target_coding_energy'][0]
            coding_energy_list.append(target_coding_energy)

            df_power.append(df)
        merged_df_power = pd.concat(df_power, ignore_index=True)
        print(merged_df_power)

        duplicate_coding_energy = np.nanmean(coding_energy_list)
        print(f'duplicate_coding_energy_list: {duplicate_coding_energy}')

        coding_energy = duplicate_coding_energy / duplicate_count
        print(f'coding_energy_list: {coding_energy_list}')
        print(f'coding_energy: {coding_energy}')

        start_time = merged_df_power.iloc[0]['time_stamp']
        end_time = merged_df_power.iloc[-1]['time_stamp']

    return start_time, end_time, count_coding, coding_energy

# cal_energy_log(coding_processes, 1)

# # replace NaT value
# for i in range(len(coding_time)):
#     if pd.isna(coding_time[i]):
#         if i + 1 < len(coding_time):
#             coding_time[i] = coding_time[i + 1]

# [[180.51, 168.96, 151.27, 163.07, 186.2, 186.11, 168.67, 154.65, 91.719, 157.31, 118.34, 91.553, 82.132, 78.699, 78.942, 79.699, 78.95, 79.259, 78.914, 78.689, 77.819, 77.189, 77.203, 76.831, 76.801, 79.185, 80.443, 81.535, 80.968, 82.552, 82.01, 86.705, 87.18299999999999, 87.976, 87.815, 94.95700000000001, 101.78, 104.75, 99.259, 93.631, 96.213, 91.03, 88.949, 88.381, 90.6, 89.859, 89.242, 87.68799999999999, 88.613]]
# [[91.178, 90.971, 95.042, 106.11, 104.36, 97.32, 95.056, 95.369, 99.993, 93.89399999999999, 95.777, 91.62899999999999, 87.609, 88.786, 87.478, 90.11399999999999, 91.181, 95.25, 90.579, 94.09100000000001, 103.49, 109.04, 95.26299999999999, 95.164, 95.193, 96.309, 92.595, 93.05, 91.005, 90.564, 91.45200000000001, 92.145, 90.507, 91.329, 92.095, 89.43, 90.68700000000001, 95.73, 110.1, 98.681, 96.824, 95.634, 99.383, 97.405, 97.78200000000001, 94.46, 88.59, 88.19, 89.38]]



# 计算时间差
count = 10
elapsed_time = 0.5
print(f'elapsed_time: {elapsed_time}')

# # 根据要求设置duplicate_count
# if elapsed_time < 10:
#     duplicate_count = max(1, int(10 / elapsed_time))
# else:
#     duplicate_count = 1  # 如果elapsed_time >= 10，将duplicate_count设置为1

duplicate_count = math.ceil(10 / elapsed_time) if 1 <= elapsed_time <= 10 else 5

print(f'duplicate count {duplicate_count}')

# 修改ffmpeg_cmd中的过滤器字符串
filter_string = f'[0:v]' * duplicate_count
print(filter_string)
filter_complex = f'"{filter_string}concat=n={duplicate_count}:v=1[v]"'
print(filter_complex)

ffmpeg_cmd = f'ffmpeg -f rawvideo -pix_fmt pixfmt -s video_widthxvideo_height -r framerate -i original_video -filter_complex {filter_complex} -map "[v]" raw_yuv_duplicate' # copy yuv file
print(ffmpeg_cmd)

