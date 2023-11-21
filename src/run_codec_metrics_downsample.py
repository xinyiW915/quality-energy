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
    count_coding = len(coding_processes)

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

    return start_time, end_time, count_coding, coding_energy

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
    total_time_list = []

    while True:

        power_log = get_power_data(cmd)
        current_power_list, current_time_list = get_power_list(power_log) #current power
        print(current_power_list)

        if meets_condition1_poweridle(current_power_list):
            logger.info('Satisfying condition 1: idle power check')
            count_repeat += 1
            coding_processes[count_repeat] = (current_power_list, current_time_list)
            consecutive_failures = 0
            total_power_list.append(current_power_list)
            total_time_list.append(current_time_list)

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
            total_power_list.append(current_power_list)
            total_time_list.append(current_time_list)
            coding_processes[consecutive_failures] = (current_power_list, current_time_list)

        if consecutive_failures >= 5:
            logger.debug(f'consecutive_failures: {consecutive_failures}')
            coding_processes[consecutive_failures] = (current_power_list, current_time_list)
            break

    return coding_processes, total_power_list, total_time_list

def measure_command_process(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    logger.debug(process)
    return process

def measure_command_runtime(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    start_time = datetime.datetime.now()
    subprocess.run(cmd, encoding="utf-8", shell=True)
    end_time = datetime.datetime.now()
    logger.info(f'start_time: {start_time}')
    logger.info(f'end_time: {end_time}')

def get_info(output, patt, info_name):
    # output_text = re.findall(findtext, output) #"bitrate:+..+kb/s"  "PSNR+......+"
    pattern = re.compile(patt)
    output_text = pattern.findall(output)
    info = "".join(output_text)
    info = info.replace(info_name, "")
    return info

def get_raw_video_bitrate(video_path):
    cmd = f'ffprobe {video_path}'
    logger.debug(f'running ffmpeg with command: {cmd}')
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.communicate()[1].decode()
    raw_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
    return raw_bitrate

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
    elif codec == 'VVC':
        if pixfmt == 'yuv420p10le':
            pixfmt_c = 'yuv420_10'
        else:
            pixfmt_c = 'yuv420'
        encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.bin'
        cmd_encode = f'vvencapp -s {video_width}x{video_height} -r {framerate} -c {pixfmt_c} -i {original_video} --preset medium -q {str(qp)} -o {encoded_video} 1>{encoded_video_log} 2>&1'

    return cmd_encode, encoded_video

def get_encoded_bitrate(encoded_video):
    cmd = f'ffprobe {encoded_video}'
    logger.debug(f'running ffmpeg with command: {cmd}')
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.communicate()[1].decode()
    encoded_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
    return encoded_bitrate

def calculate_psnr(codec_path, video, qp, framerate, video_width, video_height, pixfmt, original_video, encoded_video):
    psnr_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.csv'
    cmd_psnr = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video}' \
               f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {encoded_video} -lavfi psnr=stats_file={psnr_log} -f null -'
    logger.debug(f'running ffmpeg with command: {cmd_psnr}')
    res2 = subprocess.Popen(cmd_psnr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output2 = res2.communicate()[1].decode()
    psnr = get_info(output2, r'(?:average:)\d+\.?\d*', "average:")
    return psnr

def decoding_video(codec, video, qp, decode_path, encoded_video):
    print(f'Start {codec} Decode for {video} at crf {str(qp)}')
    logger.info(f"Start {codec} Decode for {video} at crf {str(qp)}")

    decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        cmd_decode = f'ffmpeg -i {encoded_video} -y {decode_video}'
    elif codec == 'VVC':
        cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'
    return cmd_decode, decode_video

def compute_vmaf(video, qp, vmaf_path, codec, video_width, video_height, framerate, pixfmt, original_video, decode_video):
    print('Start VMAF computation for ' + video + ' at crf' + str(qp))
    logger.info(f"Start VMAF computation for {video} at crf {str(qp)}")

    vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(qp)}_upsample_1080p.csv'
    cmd_vmaf = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video}' \
               f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video}' \
               f' -lavfi "[0:v]setpts=PTS-STARTPTS[reference]; [1:v]setpts=PTS-STARTPTS[distorted]; [distorted][reference]' \
               f'libvmaf=log_fmt=xml:log_path={vmaf_name}:model_path=../model/vmaf_v0.6.1.json:n_threads=4" ' \
               f'-f null -'

    logger.debug(f'running ffmpeg with command: {cmd_vmaf}')
    subprocess.run(cmd_vmaf, encoding="utf-8", shell=True)

    # read vmaf for decoded video
    vmaf_csv = pd.read_csv(vmaf_name)
    vmaf_line = vmaf_csv.iloc[[-4]].to_string()  # .values.tolist()
    vmaf = get_info(vmaf_line, r'(?:" mean=")\d+\.?\d*', '" mean="')

    return vmaf

def downscale_video(original_video, ugcdata_down_path, video, video_width, video_height, framerate, pixfmt):
    logger.info('Start Downsample to 540p/720p for ' + original_video)

    downsample_video_540 = f'{ugcdata_down_path}{video}_downsample_540p.yuv'
    cmd_downscale_540 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=960:540:flags=lanczos -s:v 960x540 -r {framerate} -pix_fmt {pixfmt} {downsample_video_540}'
    logger.debug(f'running ffmpeg with command: {cmd_downscale_540}')
    subprocess.run(cmd_downscale_540, encoding="utf-8", shell=True)

    downsample_video_720 = f'{ugcdata_down_path}{video}_downsample_720p.yuv'
    cmd_downscale_720 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=1280:720:flags=lanczos -s:v 1280x720 -r {framerate} -pix_fmt {pixfmt} {downsample_video_720}'
    logger.debug(f'running ffmpeg with command: {cmd_downscale_720}')
    subprocess.run(cmd_downscale_720, encoding="utf-8", shell=True)

    return downsample_video_540, downsample_video_720


def upscale_video(downsample_video, qp, upscale_path, codec, width, height, framerate, pixfmt, decode_video):
    logger.info('Start Upsample to 1080p for ' + downsample_video + ' at crf' + str(qp))

    upsample_video_yuv = f'{upscale_path}{codec}/{downsample_video}_decoded_crf_{str(qp)}_upsample_1080p.yuv'
    cmd_upscale = f'ffmpeg -s:v {width}x{height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video} -vf scale=1920:1080:flags=lanczos -s:v 1920x1080 -r {framerate} -pix_fmt {pixfmt} {upsample_video_yuv}'
    subprocess.run(cmd_upscale, encoding="utf-8", shell=True)

    return upsample_video_yuv

if __name__ == '__main__':
    # logging config
    with open('logging.yml', 'r') as file_logging:
        dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
    logging.config.dictConfig(dict_conf)
    logger = logging.getLogger('default')
    logger.info('This is a log info for video codecs')

    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_1080P_metadata_downsample.csv")

    ugcdata_ori_path = '../ugc-dataset/'
    ugcdata_down_path = '../videocodec_downsample_1080p/downsample_ugc/'
    encode_path = '../videocodec_downsample_1080p/encode/'
    decode_path = '../videocodec_downsample_1080p/decode/'
    upscale_path = '../videocodec_downsample_1080p/upscale/'
    ffmpeg_path = '../videocodec_downsample_1080p/ffmpeg/'
    original_path = '../videocodec_downsample_1080p/input/'
    vmaf_path = '../videocodec_downsample_1080p/vmaf/'

    codec = 'SVT-AV1'
    codec_path = f'{ffmpeg_path}{codec}/'
    if codec == 'x265':
        codec_name = 'libx265'
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
    elif codec == 'x264':
        codec_name = 'libx264'
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
    elif codec == 'VP9':
        codec_name = 'libvpx-vp9'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
    elif codec == 'SVT-AV1':
        codec_name = 'libsvtav1'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]

    df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framrate',
                                       'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP',
                                       'duplicate_bitrate_rawvideo (kb/s)',
                                       'start_time_encode', 'end_time_encode', 'count_encode',
                                       'start_time_decode', 'end_time_decode', 'count_decode',
                                       'target_encode_energy', 'decode_energy', 'total_energy'])

    # compute the metrics
    vid_list = []
    cate_list = []
    res_list = []
    width_list = []
    height_list = []
    pix_list = []
    fps_list = []
    bitrate_raw_list = []
    bitrate_encoded_list = []
    psnr_list = []
    vmaf_list = []
    qp_list = []

    # compute the energy
    duplicate_bitrate_raw_list = []
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
    df_encoding_power = pd.DataFrame(columns=['vid', 'time_stamp', 'power'])
    df_decoding_power = pd.DataFrame(columns=['vid', 'time_stamp', 'power'])
    total_encoding_power_list = []
    total_encoding_time_list = []
    total_decoding_power_list = []
    total_decoding_time_list = []
    
    for i in range(len(ugcdata)):
        video = ugcdata['vid'][i]
        category = ugcdata['category'][i]
        resolution = ugcdata['resolution'][i]
        video_width = ugcdata['width'][i]
        video_height = ugcdata['height'][i]
        pixfmt = ugcdata['pixfmt'][i]
        framerate = ugcdata['framerate'][i]

        # read bitrate for raw video
        raw_video = f'{ugcdata_ori_path}{video}.mkv'
        raw_bitrate = get_raw_video_bitrate(raw_video)

        print(f'--------------------Run the process for {codec}------------------------')
        logger.info(f"Starting with encoder {codec}")
        video_name = f'{video}.mkv'
        original_video = f'{original_path}{video}.yuv'

        # --------------------Convert mkv to yuv------------------------
        convert_mkv_to_yuv(video_name, ugcdata_ori_path, original_video, pixfmt)

        # --------------------Downsample to 540p/720p------------------------
        downsample_video_540, downsample_video_720 = downscale_video(original_video, ugcdata_down_path, video, video_width, video_height, framerate, pixfmt)
        downsample_video_list = [f'{video}_downsample_540p', f'{video}_downsample_720p']
        downsample_width_list = [960, 1280]
        downsample_height_list = [540, 720]
        result_list = [(downsample_video, qp, downsample_width, downsample_height) for downsample_video, downsample_width, downsample_height in
                       zip(downsample_video_list, downsample_width_list, downsample_height_list) for qp in qp_level]

        # --------------------Calcultate quality------------------------
        for downsample_video, qp, downsample_width, downsample_height in result_list:
            vid_list.append(downsample_video)
            cate_list.append(category)
            res_list.append(downsample_height)
            width_list.append(downsample_width)
            height_list.append(downsample_height)
            pix_list.append(pixfmt)
            fps_list.append(framerate)
            bitrate_raw_list.append(raw_bitrate)
            qp_list.append(qp)

            if downsample_height == 540:
                downsample_video_yuv = downsample_video_540
            elif downsample_height == 720:
                downsample_video_yuv = downsample_video_720

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video = encoding_video(codec, downsample_video, qp, framerate, downsample_width, downsample_height, pixfmt, downsample_video_yuv, encode_path)
            measure_command_runtime(cmd_encode)

            # ------------------------read bitrate for encoded video------------------------
            encoded_bitrate = get_encoded_bitrate(encoded_video)
            bitrate_encoded_list.append(encoded_bitrate)

            # --------------------Start Decode------------------------
            cmd_decode, decode_video = decoding_video(codec, downsample_video, qp, decode_path, encoded_video)
            measure_command_runtime(cmd_decode)

            # --------------------Upsample to 1080p------------------------
            upsample_video_yuv = upscale_video(downsample_video, qp, upscale_path, codec, downsample_width, downsample_height, framerate, pixfmt, decode_video)

            # ------------------------read psnr for encoded video------------------------
            psnr = calculate_psnr(codec_path, downsample_video, qp, framerate, video_width, video_height, pixfmt, original_video, upsample_video_yuv)
            psnr_list.append(psnr)

            # --------------------VMAF computaion------------------------
            vmaf = compute_vmaf(downsample_video, qp, vmaf_path, codec, video_width, video_height, framerate, pixfmt, original_video, upsample_video_yuv)
            vmaf_list.append(vmaf)

            # remove input and decoded files for saving space
            os.remove(encoded_video)
            os.remove(decode_video)
            os.remove(upsample_video_yuv)
        os.remove(downsample_video_540)
        os.remove(downsample_video_720)
        os.remove(original_video)



        # --------------------Calcultate energy------------------------
        duplicate_path = f'{ugcdata_down_path}duplicate/'
        duplicate_video = f'{video}_duplicate'

        raw_duplicate = f'{duplicate_path}{duplicate_video}.mkv'

        print(f'--------------------Run the energy measurement process for {codec}------------------------')
        logger.info(f"Run the energy measurement process for {codec}")
        duplicate_video_name = f'{duplicate_video}.mkv'
        original_duplicate = f'{original_path}{duplicate_video}.yuv'

        # duplicate mkv 6/12/24 times
        repeat_count = 5
        duplicate_count = repeat_count + 1
        ffmpeg_cmd = f'ffmpeg -stream_loop {repeat_count} -y -i {raw_video} -c copy {raw_duplicate}'
        subprocess.call(ffmpeg_cmd, shell=True)

        # read bitrate for raw duplicate video
        raw_bitrate_duplicate = get_raw_video_bitrate(raw_duplicate)

        # --------------------Convert mkv to yuv------------------------
        convert_mkv_to_yuv(duplicate_video_name, duplicate_path, original_duplicate, pixfmt)

        # --------------------Downsample to 540p/720p------------------------
        downsample_duplicate_540, downsample_duplicate_720 = downscale_video(original_duplicate, ugcdata_down_path, duplicate_video, video_width, video_height, framerate, pixfmt)

        downsample_duplicate_list = [f'{duplicate_video}_downsample_540p', f'{duplicate_video}_downsample_720p']
        downsample_width_list = [960, 1280]
        downsample_height_list = [540, 720]
        result_list = [(downsample_duplicate, qp, downsample_width, downsample_height) for downsample_duplicate, downsample_width, downsample_height in
                       zip(downsample_duplicate_list, downsample_width_list, downsample_height_list) for qp in qp_level]

        for downsample_duplicate, qp, downsample_width, downsample_height in result_list:
            duplicate_bitrate_raw_list.append(raw_bitrate_duplicate)

            if downsample_height == 540:
                downsample_duplicate_yuv = downsample_duplicate_540
            elif downsample_height == 720:
                downsample_duplicate_yuv = downsample_duplicate_720

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video = encoding_video(codec, downsample_duplicate, qp, framerate, downsample_width, downsample_height, pixfmt, downsample_duplicate_yuv, encode_path)

            ## ------------------------get power log for encoding process------------------------
            logger.info(f'get power log for encoding process')
            encoding_processes, encoding_power_list, encoding_time_list = measure_command_runtime_distribution(cmd_encode)
            
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
            decoding_processes, decoding_power_list, decoding_time_list = measure_command_runtime_distribution(cmd_decode)
            
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
            total_decoding_power_list.append(decoding_power_list)
            total_decoding_time_list.append(decoding_time_list)

            # remove input and decoded files for saving space
            os.remove(encoded_video)
            os.remove(decode_video)
            os.remove('../metrics/energy_log/power_log.csv')
        os.remove(downsample_duplicate_540)
        os.remove(downsample_duplicate_720)
        # os.remove(raw_duplicate)
        os.remove(original_duplicate)


    # metrics and energy log
    df_metrics['vid'] = vid_list
    df_metrics['category'] = cate_list
    df_metrics['resolution'] = res_list
    df_metrics['width'] = width_list
    df_metrics['height'] = height_list
    df_metrics['pixfmt'] = pix_list
    df_metrics['framrate'] = fps_list
    df_metrics['bitrate_rawvideo (kb/s)'] = bitrate_raw_list
    df_metrics['bitrate_encoded (kb/s)'] = bitrate_encoded_list
    df_metrics['PSNR'] = psnr_list
    df_metrics['VMAF'] = vmaf_list
    df_metrics['QP'] = qp_list

    df_metrics['duplicate_bitrate_rawvideo (kb/s)'] = duplicate_bitrate_raw_list
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
    metrics_name = f'../videocodec_downsample_1080p/YOUTUBE_UGC_1080P_downsample_{codec}_metrics_timestamp_duplicate_distribution_energy.csv'
    df_metrics.to_csv(metrics_name, index=None)
    
    # keep power log
    df_encoding_power['vid'] = vid_list
    df_encoding_power['power'] = total_encoding_power_list
    df_encoding_power['time_stamp'] = total_encoding_time_list
    df_encoding_power_name = f'../metrics/energy_log/YOUTUBE_UGC_1080P_downsample_{codec}_encoding_power_log.csv'
    df_encoding_power.to_csv(df_encoding_power_name, index=None)

    df_decoding_power['vid'] = vid_list
    df_decoding_power['power'] = total_decoding_power_list
    df_decoding_power['time_stamp'] = total_decoding_time_list
    df_decoding_power_name = f'../metrics/energy_log/YOUTUBE_UGC_1080P_downsample_{codec}_decoding_power_log.csv'
    df_decoding_power.to_csv(df_decoding_power_name, index=None)

