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
from analysis.endtime_none_tek_net import coding_process, power_measurement, run_parallel_processes, \
    stop_remote_process, powerlog_copy
from functools import partial
from analysis.task_energy import calc_energies_on_dataframe, calc_job_energy_on_job_row, \
    calc_job_energy_on_job_row_single

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
    print(f'coding_processes: {coding_processes}')
    count_coding = len(coding_processes)
    print(f'count_repeat: {count_coding}')
    print("==================================================================")

    df_power = []
    coding_energy_list = []
    repeat_count = 0

    for key, value in coding_processes.items():
        df = pd.DataFrame({'power': value[0], 'time_stamp': value[1]})
        coding_power, coding_time = get_power_list(df)

        repeat_count += 1
        print(str(repeat_count) + ' times')
        logger.info(f'coding_power: {coding_power}')
        logger.info(f'coding_time: {coding_time}')

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

    return start_time, end_time, count_coding, coding_energy

def meets_condition1_poweridle(power_list):
    # Average idle power
    power_idle = 76.2
    # Threshold value
    threshold = 1.05
    power_array = np.array(power_list)

    if len(power_array) != 0:
        average_power = sum(power_array) / len(power_array)
        logger.info(f'total average power: {average_power}')
        condition1 = average_power > power_idle * threshold

        if condition1:
            window_size = 3  # Size of the moving window
            num_below_threshold = 0  # Counter for moving average below threshold

            if len(power_array) >= window_size:
                for i in range(len(power_array) - window_size + 1):
                    window = power_array[i:i + window_size]
                    moving_average = np.mean(window)
                    logger.info(f'moving average: {moving_average}')
                    if moving_average < power_idle * threshold:
                        num_below_threshold += 1
                        if num_below_threshold > 6:
                            logger.info(f'More than 6 times the moving average < idel power * threshold  \n')
                            return False  # break if condition2 is not met

            return True  # If we reach here, both conditions are met
        else:
            logger.info(f'total average power < idel power * threshold')
            return False  # If condition1 is not met, return False
    else:
        logger.debug('Power list is empty')
        return False

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

def measure_command_runtime_distribution(cmd, repeat_time, old_video_path):
    logger.debug(f'running ffmpeg with command: {cmd}')

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

        logger.debug("==================================================================")
        logger.info(str(i + 1) + ' times')
        tmp_power_list = []

        while True:
            power_log = get_power_data(cmd)
            current_power_list, current_time_list = get_power_list(power_log)  # current power
            logger.info(f'current_power_list: {current_power_list}')

            total_power_log = pd.concat([total_power_log, power_log])
            logger.info(f'total_power_log: {total_power_log}')

            if current_power_list == []:
                break

            if meets_condition1_poweridle(current_power_list):
                logger.info('Satisfying condition 1: idle power check')
                count_repeat += 1
                total_power_list.append(current_power_list)
                total_time_list.append(current_time_list)
                coding_processes[count_repeat] = (current_power_list, current_time_list)

                tmp_power_list.append(current_power_list)

                # Check the distribution condition
                # put a logging (keep the measurement of formula inequality sides)
                measure, left_side, right_side = meets_condition2_tdistribution(tmp_power_list)
                if measure:
                    logger.info('Satisfying condition 2: t-distribution')
                    break
                elif count_repeat > 100:
                    logger.error('Timed out, count_repeat > 100')
                    break  # count_repeat >100 we break the loop #take the logging notes
                else:
                    print('Not satisfying condition 2: t-distribution. Retrying...\n')

            else:
                consecutive_failures += 1
                logger.debug(f'consecutive_failures: {consecutive_failures}')
                failure_power_list.append(current_power_list)
                failure_time_list.append(current_time_list)
                logger.info(f'failure_power_list: {current_power_list}')
                logger.info(f'failure_time_list: {current_time_list}')

            if consecutive_failures >= 5:
                logger.debug(f'consecutive_failures: {consecutive_failures}')
                break

    return coding_processes, total_power_list, total_time_list, failure_power_list, failure_time_list

def measure_command_process(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    logger.debug(process)
    return process

def convert_mkv_to_yuv(video_name, video_path, original_video, pixfmt):
    print('Convert mkv to yuv ' + video_name)
    logger.info(f"Convert mkv to yuv for {video_name}")
    cmd_convert = f'ffmpeg -y -i {video_path + video_name} -c:v rawvideo -pixel_format {pixfmt} {original_video}'  # change that
    process_convert = measure_command_process(cmd_convert)
    if process_convert.returncode != 0:
        logger.error('error: process.returncode != 0')
        raise ValueError(process_convert.stdout)

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

    return cmd_encode, encoded_video

def decoding_video(codec, video, qp, decode_path, encoded_video):
    print(f'Start {codec} Decode for {video} at crf {str(qp)}')
    logger.info(f"Start {codec} Decode for {video} at crf {str(qp)}")

    decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
    decoded_video_log = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.txt'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        # cmd_decode = f'ffmpeg -i {encoded_video} -y -f rawvideo {decode_video} 1>{decoded_video_log} 2>&1' #-f: not allow to put in the standard output.
        cmd_decode = f'time ffmpeg -i {encoded_video} -benchmark -y -f null - 1>{decoded_video_log} 2>&1' #-f: not allow to put in the standard output.

    return cmd_decode, decode_video

def downscale_video(original_video, ugcdata_down_path, video, video_width, video_height, framerate, pixfmt):
    logger.info('Start Downsample to 1080p/720p for ' + original_video)

    downsample_video_1080 = f'{ugcdata_down_path}{video}_downsample_1080p.yuv'
    cmd_downscale_1080 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=1920:1080:flags=lanczos -s:v 1920x1080 -r {framerate} -pix_fmt {pixfmt} {downsample_video_1080}'
    logger.debug(f'running ffmpeg with command: {cmd_downscale_1080}')
    subprocess.run(cmd_downscale_1080, encoding="utf-8", shell=True)

    # downsample_video_720 = f'{ugcdata_down_path}{video}_downsample_720p.yuv'
    # cmd_downscale_720 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=1280:720:flags=lanczos -s:v 1280x720 -r {framerate} -pix_fmt {pixfmt} {downsample_video_720}'
    # logger.debug(f'running ffmpeg with command: {cmd_downscale_720}')
    # subprocess.run(cmd_downscale_720, encoding="utf-8", shell=True)

    # downsample_video_1080, downsample_video_720
    return downsample_video_1080

if __name__ == '__main__':
    # logging config
    with open('logging_4k.yml', 'r') as file_logging:
        dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
    logging.config.dictConfig(dict_conf)
    logger = logging.getLogger('default')
    logger.info("\n ==================================================================")
    logger.info('This is a log info for video codecs')

    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_2160P_metadata_downsample.csv")

    ugcdata_ori_path = '../ugc-dataset/2160P/'
    ugcdata_down_path = '../videocodec_downsample_4k/downsample_ugc/'
    encode_path = '../videocodec_downsample_4k/test_decoding/encode/'
    decode_path = '../videocodec_downsample_4k/test_decoding/decode/'
    original_path = '../videocodec_downsample_4k/input/'

    df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framerate',
                                       'start_time_encode', 'end_time_encode', 'count_encode',
                                       'start_time_decode', 'end_time_decode', 'count_decode'])

    # compute the metrics
    vid_list = []
    cate_list = []
    res_list = []
    width_list = []
    height_list = []
    pix_list = []
    fps_list = []

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

    # keep power log
    df_encoding_power = pd.DataFrame(columns=['vid', 'time_stamp', 'power', 'failure_encoding_power', 'failure_encoding_time'])
    df_decoding_power = pd.DataFrame(columns=['vid', 'time_stamp', 'power', 'failure_decoding_power', 'failure_decoding_time'])
    total_encoding_power_list = []
    total_encoding_time_list = []
    total_failure_encoding_power_list = []
    total_failure_encoding_time_list = []

    total_decoding_power_list = []
    total_decoding_time_list = []
    total_failure_decoding_power_list = []
    total_failure_decoding_time_list = []

    codec = 'x264'
    if codec == 'x264':
        codec_name = 'libx264'
        qp_level = [10,20,30,40,50]

    for i in range(len(ugcdata)):
        video = ugcdata['vid'][i]
        category = ugcdata['category'][i]
        resolution = ugcdata['resolution'][i]
        video_width = ugcdata['width'][i]
        video_height = ugcdata['height'][i]
        pixfmt = ugcdata['pixfmt'][i]
        framerate = ugcdata['framerate'][i]

        print(f'--------------------Run the energy measurement process for {codec}------------------------')
        logger.info(f'------------------------------------------------------------------------------------')
        logger.info(f"Run the energy measurement process for {codec}")
        video_name = f'{video}.mkv'
        original_video = f'{original_path}{video}.yuv'

        # --------------------Convert mkv to yuv------------------------
        convert_mkv_to_yuv(video_name, ugcdata_ori_path, original_video, pixfmt)

        print(f'--------------------Run the energy measurement process with downsampling for {codec}------------------------')
        # --------------------Downsample to 1080p/720p------------------------
        downsample_video_1080 = downscale_video(original_video, ugcdata_down_path, video,
                                                                             video_width, video_height, framerate, pixfmt)
        # downsample_video_720

        downsample_video_list = [f'{video}_downsample_1080p', f'{video}_downsample_720p']
        downsample_width_list = [1920, 1280]
        downsample_height_list = [1080, 720]
        # downsample_video_list = [f'{video}_downsample_720p']
        # downsample_width_list = [1280]
        # downsample_height_list = [720]
        result_list = [(downsample_video, qp, downsample_width, downsample_height) for
                       downsample_video, downsample_width, downsample_height in
                       zip(downsample_video_list, downsample_width_list, downsample_height_list) for qp in qp_level]

        for index, (downsample_video, qp, downsample_width, downsample_height) in enumerate(result_list):
            vid_list.append(downsample_video)
            cate_list.append(category)
            res_list.append(downsample_height)
            width_list.append(downsample_width)
            height_list.append(downsample_height)
            pix_list.append(pixfmt)
            fps_list.append(framerate)

            logger.info(f"Index: {index}, downsample_video: {downsample_video}, qp: {qp}, downsample_width: {downsample_width}, downsample_height: {downsample_height}")

            repeat_time = 10
            duplicate_count = 10 # ceil.
            logger.info(f"duplicate_count: {duplicate_count}")

            if downsample_height == 1080:
                downsample_video_yuv = downsample_video_1080
            elif downsample_height == 720:
                downsample_video_yuv = downsample_video_720

            duplicate_path = f'{ugcdata_down_path}duplicate/'
            downsample_duplicate = f'{downsample_video}_duplicate'
            downsample_duplicate_yuv = f'{duplicate_path}{downsample_duplicate}.yuv'

            # duplicate the video
            filter_string = f'[0:v]' * duplicate_count
            filter_complex = f'"{filter_string}concat=n={duplicate_count}:v=1[v]"'
            cmd_duplicate = f'ffmpeg -f rawvideo -pix_fmt {pixfmt} -s {downsample_width}x{downsample_height} -r {framerate} -y -i {downsample_video_yuv} -filter_complex {filter_complex} -map "[v]" {downsample_duplicate_yuv}'
            subprocess.call(cmd_duplicate, shell=True)
            logger.debug(f'running ffmpeg with command: {cmd_duplicate}')

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video = encoding_video(codec, downsample_duplicate, qp, framerate, downsample_width,
                                                       downsample_height, pixfmt, downsample_duplicate_yuv, encode_path)

            ## ------------------------get power log for encoding process------------------------
            logger.info(f'get power log for encoding process')
            encoding_processes, encoding_power_list, encoding_time_list, failure_encoding_power_list, failure_encoding_time_list = measure_command_runtime_distribution(cmd_encode, repeat_time, encoded_video)

            start_time_encode, end_time_encode, count_encode, encode_energy = cal_energy_log(encoding_processes, duplicate_count)
            logger.info(f'start_time_encode: {start_time_encode}')
            logger.info(f'end_time_encode: {end_time_encode}')
            logger.info(f'count_encode: {count_encode}')

            start_time_encode_list.append(start_time_encode)
            end_time_encode_list.append(end_time_encode)
            count_encode_list.append(count_encode)
            encode_energy_list.append(encode_energy)

            # --------------------Start Decode------------------------
            cmd_decode, decode_video = decoding_video(codec, downsample_duplicate, qp, decode_path, encoded_video)

            ## ------------------------get power log for decoding process------------------------
            logger.info(f'get power log for decoding process')
            decoding_processes, decoding_power_list, decoding_time_list, failure_decoding_power_list, failure_decoding_time_list = measure_command_runtime_distribution(cmd_decode, repeat_time, decode_video)

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

            # keep power log
            total_encoding_power_list.append(encoding_power_list)
            total_encoding_time_list.append(encoding_time_list)
            total_failure_encoding_power_list.append(failure_encoding_power_list)
            total_failure_encoding_time_list.append(failure_encoding_time_list)

            total_decoding_power_list.append(decoding_power_list)
            total_decoding_time_list.append(decoding_time_list)
            total_failure_decoding_power_list.append(failure_decoding_power_list)
            total_failure_decoding_time_list.append(failure_decoding_time_list)

            # remove input and decoded files for saving space
            # os.remove(encoded_video)
            # os.remove(decode_video)
            # os.remove(downsample_duplicate_yuv)
            os.remove('../metrics/energy_log/power_log.csv')
        # os.remove(downsample_video_1080)
        # os.remove(downsample_video_720)
        os.remove(original_video)

    # metrics
    df_metrics['vid'] = vid_list
    df_metrics['category'] = cate_list
    df_metrics['resolution'] = res_list
    df_metrics['width'] = width_list
    df_metrics['height'] = height_list
    df_metrics['pixfmt'] = pix_list
    df_metrics['framerate'] = fps_list

    # energy log
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
    energy_name = f'../videocodec_downsample_4k/test_decoding/YOUTUBE_UGC_2160P_downsample_{codec}_metrics_timing_decoding_{category}.csv'
    df_metrics.to_csv(energy_name, index=None)

    # keep power log
    print(total_failure_encoding_power_list)
    df_encoding_power['vid'] = vid_list
    df_encoding_power['power'] = total_encoding_power_list
    df_encoding_power['time_stamp'] = total_encoding_time_list
    df_encoding_power['failure_encoding_power'] = total_failure_encoding_power_list
    df_encoding_power['failure_encoding_time'] = total_failure_encoding_time_list
    df_encoding_power_name = f'../videocodec_downsample_4k/test_decoding/YOUTUBE_UGC_2160P_downsample_{codec}_repeat_duplicate_encoding_power_log.csv'
    df_encoding_power.to_csv(df_encoding_power_name, index=None)

    df_decoding_power['vid'] = vid_list
    df_decoding_power['power'] = total_decoding_power_list
    df_decoding_power['time_stamp'] = total_decoding_time_list
    df_decoding_power['failure_decoding_power'] = total_failure_decoding_power_list
    df_decoding_power['failure_decoding_time'] = total_failure_decoding_time_list
    df_decoding_power_name = f'../videocodec_downsample_4k/test_decoding/YOUTUBE_UGC_2160P_downsample_{codec}_repeat_duplicate_decoding_power_log.csv'
    df_decoding_power.to_csv(df_decoding_power_name, index=None)