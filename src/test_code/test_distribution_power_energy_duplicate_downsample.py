import datetime
from datetime import timedelta
import time
import subprocess
from fabric import Connection
import paramiko
from scipy import stats
import pandas as pd
import numpy as np
import math
import re
import os
import logging.config
import logging
import yaml
import shlex

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

from dateutil.parser import parse
from analysis.endtime_none_tek_net import coding_process, power_measurement, run_parallel_processes, stop_remote_process, powerlog_copy
from functools import partial
from analysis.task_energy import calc_energies_on_dataframe, calc_job_energy_on_job_row, calc_job_energy_on_job_row_single


def get_power_data(cmd):
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key
    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    logger.debug('code sleep 10 secs')
    time.sleep(10)
    run_parallel_processes(cmd)
    stop_remote_process(conn, 'python')
    logger.debug('code sleep 1 secs')
    time.sleep(1)

    power_log = powerlog_copy(conn)

    return power_log


def get_power_list(power_log):
    time_list = power_log['time_stamp'].tolist()
    power_list = power_log['power'].tolist()
    return power_list, time_list


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

    _calc_job_energy_target_coding = partial(calc_job_energy_on_job_row_single, df_power_e,
                                             lambda x: x['target_coding']['start_time'],
                                             lambda x: x['target_coding']['end_time'])
    df['target_coding_energy'] = df.apply(_calc_job_energy_target_coding, axis=1)

    return df


def cal_energy_log(coding_processes, duplicate_count):
    count_repeat = len(coding_processes)

    df_power = []
    coding_energy_list = []

    for key, value in coding_processes.items():
        df = pd.DataFrame({'power': value[0], 'time_stamp': value[1]})
        coding_power, coding_time = get_power_list(df)
        logger.info(f'coding_power: {coding_power}')
        logger.info(f'coding_time: {coding_time}')
        print("==================================================================")

        df_energy = test_calc_job_energy(coding_power, coding_time)
        logger.info(f'df_energy: {df_energy.T}')
        print("==================================================================")
        target_coding_energy = df_energy['target_coding_energy'][0]
        coding_energy_list.append(target_coding_energy)

        df_power.append(df)
    merged_df_power = pd.concat(df_power, ignore_index=True)

    duplicate_coding_energy = np.nanmean(coding_energy_list)
    logger.info(f'duplicate_coding_energy_list: {duplicate_coding_energy}')

    coding_energy = duplicate_coding_energy / duplicate_count
    logger.info(f'coding_energy_list: {coding_energy_list}')
    logger.info(f'coding_energy: {coding_energy}')

    start_time = merged_df_power.iloc[0]['time_stamp']
    end_time = merged_df_power.iloc[-1]['time_stamp']

    return start_time, end_time, count_repeat, coding_energy


def meets_condition1_poweridle(power_list):
    power_array = np.array(power_list)
    if len(power_array) != 0:
        # Average idle power
        power_idle = 80
        # Threshold value
        threshold = 1.05
        average_power = sum(power_array) / len(power_array)
        condition1 = average_power > power_idle * threshold
    else:
        logger.error('Power list is empty')
        condition1 = False

    return condition1


def meets_condition2_tdistribution(power_list):
    flat_list = [item for sublist in power_list for item in sublist]
    power_array = np.array(flat_list)
    logger.debug(f'power_array: {power_array}')
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
        logger.info(f'left_side of the equation:{left_side}')
        logger.info((f'right side of the equation: {right_side}'))
    else:
        logger.error('Power list is empty')
        condition2 = False
        left_side = None
        right_side = None
        logger.info(f'left_side of the equation:{left_side}')
        logger.info((f'right side of the equation: {right_side}'))

    return condition2, left_side, right_side


def measure_command_runtime_distribution(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    count_repeat = 0
    coding_processes = {}
    consecutive_failures = 0
    total_power_list = []

    while True:

        power_log = get_power_data(cmd)
        current_power_list, time_list = get_power_list(power_log)  # current power

        if meets_condition1_poweridle(current_power_list):
            logger.info('Satisfying condition 1: idle power check')
            total_power_list.append(current_power_list)
            count_repeat += 1
            coding_processes[count_repeat] = (current_power_list, time_list)
            consecutive_failures = 0

            # put a logging (keep the measurement of formula inequality sides)
            measure, left_side, right_side = meets_condition2_tdistribution(total_power_list)
            if measure:
                logger.info('Satisfying condition 2: t-distribution')
                break
            elif count_repeat > 100:
                logger.error('Timed out, count_repeat > 100')
                break  # count_repeat >100 we break the loop #take the logging notes
        else:
            consecutive_failures += 1
            logger.debug(f'consecutive_failures: {consecutive_failures}')

        if consecutive_failures >= 5:
            logger.debug(f'consecutive_failures: {consecutive_failures}')
            coding_processes[0] = (current_power_list, time_list)
            break

    return coding_processes

def encoding_video(codec, video, qp, framerate, video_width, video_height, pixfmt, original_video, encode_path):
    print(f'Start {codec} Encode for {video} at crf {qp}, fps: {framerate}')
    logger.debug(f"Start {codec} Encode for {video} at crf {qp}, fps: {framerate}")

    encoded_video_log = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.txt'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        if codec == 'VP9':
            encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.webm'
        else:
            encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.mp4'
        cmd_encode = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -y -i {original_video} -c:v {codec_name}' \
                     f' -crf {str(qp)} {encoded_video} 1>{encoded_video_log} 2>&1'
    elif codec == 'VVC':
        if pixfmt == 'yuv420p10le':
            pixfmt_c = 'yuv420_10'
        else:
            pixfmt_c = 'yuv420'
        encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.bin'
        cmd_encode = f'vvencapp -s {video_width}x{video_height} -r {framerate} -c {pixfmt_c} -i {original_video} --preset medium -q {str(qp)} -o {encoded_video} 1>{encoded_video_log} 2>&1'

    return cmd_encode, encoded_video


def decoding_video(codec, video, qp, decode_path, encoded_video):
    print(f'Start {codec} Decode for {video} at crf {str(qp)}')
    logger.info(f"Start {codec} Decode for {video} at crf {str(qp)}")

    decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        cmd_decode = f'ffmpeg -i {encoded_video} -y {decode_video}'
    elif codec == 'VVC':
        cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'
    return cmd_decode, decode_video


if __name__ == '__main__':
    # logging config
    with open('logging.yml', 'r') as file_logging:
        dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
    logging.config.dictConfig(dict_conf)
    logger = logging.getLogger('default')
    logger.info('This is a log info for video codecs')

    ugcdata = pd.read_csv("../ugc-dataset/downsample/YOUTUBE_UGC_1080P_metadata_downsample_copy.csv")

    ugcdata_path = '../ugc-dataset/downsample/downsample_ugc/'
    encode_path = '../ugc-dataset/downsample/encode/'
    decode_path = '../ugc-dataset/downsample/decode/'
    upscale_path = '../ugc-dataset/downsample/upscale/'
    ffmpeg_path = '../ugc-dataset/downsample/ffmpeg/'
    original_path = '../ugc-dataset/downsample/input/'
    vmaf_path = '../ugc-dataset/downsample/vmaf/'

    codec = 'SVT-AV1'

    if codec == 'SVT-AV1':
        codec_name = 'libsvtav1'  # 'libaom-av1' #'libsvtav1'
        # qp_level = [12]
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]

    df_metrics = pd.DataFrame(
        columns=['vid', 'QP',
                 'start_time_encode', 'end_time_encode', 'count_encode',
                 'start_time_decode', 'end_time_decode', 'count_decode',
                 'target_encode_energy', 'decode_energy', 'total_energy'])

    vid_list = []
    qp_list = []

    # compute the energy
    start_time_encode_list = []
    end_time_encode_list = []
    count_encode_list = []
    start_time_decode_list = []
    end_time_decode_list = []
    count_decode_list = []
    encode_energy_list = []
    decode_energy_list = []
    total_energy_list = []

    for i in range(len(ugcdata)):
        video = ugcdata['vid'][i]
        category = ugcdata['category'][i]
        resolution = ugcdata['resolution'][i]
        video_width = ugcdata['width'][i]
        video_height = ugcdata['height'][i]
        pixfmt = ugcdata['pixfmt'][i]
        framerate = ugcdata['framerate'][i]

        # --------------------Calcultate energy------------------------
        duplicate_path = f'{ugcdata_path}duplicate/'
        duplicate_video = f'{video}_duplicate'

        raw_duplicate = f'{duplicate_path}{duplicate_video}.mkv'

        print(f'--------------------Run the energy measurement process for {codec}------------------------')
        logger.info(f"Run the energy measurement process for {codec}")
        duplicate_video_name = f'{duplicate_video}.mkv'
        original_duplicate = f'{original_path}{duplicate_video}.yuv'
        
        # duplicate mkv 6 times
        repeat_count = 5
        duplicate_count = repeat_count + 1
        
        for qp in qp_level:
            vid_list.append(video)
            qp_list.append(qp)

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video = encoding_video(codec, duplicate_video, qp, framerate, video_width, video_height, pixfmt, original_duplicate, encode_path)

            ## ------------------------get power log for encoding process------------------------
            logger.info(f'get power log for encoding process')
            encoding_processes = measure_command_runtime_distribution(cmd_encode)
            start_time_encode, end_time_encode, count_encode, encode_energy = cal_energy_log(encoding_processes, duplicate_count)

            logger.info(f'start_time_encode: {start_time_encode}')
            logger.info(f'end_time_encode: {end_time_encode}')
            logger.info(f'count_encode: {count_encode}')

            start_time_encode_list.append(start_time_encode)
            end_time_encode_list.append(end_time_encode)
            count_encode_list.append(count_encode)
            encode_energy_list.append(encode_energy)

            # --------------------Start Decode------------------------
            cmd_decode, decode_video = decoding_video(codec, duplicate_video, qp, decode_path, encoded_video)

            ## ------------------------get power log for decoding process------------------------
            logger.info(f'get power log for decoding process')
            decoding_processes = measure_command_runtime_distribution(cmd_decode)
            start_time_decode, end_time_decode, count_decode, decode_energy = cal_energy_log(decoding_processes, duplicate_count)

            logger.info(f'start_time_decode: {start_time_decode}')
            logger.info(f'end_time_decode: {end_time_decode}')
            logger.info(f'count_decode: {count_decode}')

            start_time_decode_list.append(start_time_decode)
            end_time_decode_list.append(end_time_decode)
            count_decode_list.append(count_decode)
            decode_energy_list.append(decode_energy)

            total_energy = encode_energy + decode_energy
            total_energy_list.append(total_energy)

            # remove input and decoded files for saving space
            os.remove(encoded_video)
            os.remove(decode_video)
            os.remove('../metrics/energy_log/power_log.csv')
        # os.remove(raw_duplicate)
        # os.remove(original_duplicate)



    df_metrics['vid'] = vid_list
    df_metrics['QP'] = qp_list

    df_metrics['start_time_encode'] = start_time_encode_list
    df_metrics['end_time_encode'] = end_time_encode_list
    df_metrics['count_encode'] = count_encode_list
    df_metrics['start_time_decode'] = start_time_decode_list
    df_metrics['end_time_decode'] = end_time_decode_list
    df_metrics['count_decode'] = count_decode_list
    df_metrics['target_encode_energy'] = encode_energy_list
    df_metrics['decode_energy'] = decode_energy_list
    df_metrics['total_energy'] = total_energy_list

    print(df_metrics)
    metrics_name = f'../ugc-dataset/downsample/YOUTUBE_UGC_1080P_downsample_{codec}_timestamp_duplicate_distribution_energy.csv'
    df_metrics.to_csv(metrics_name, index=None)