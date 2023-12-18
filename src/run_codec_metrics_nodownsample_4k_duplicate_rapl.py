import datetime
from datetime import timedelta
import time
from dateutil.parser import parse
import subprocess
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
import shutil

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")
from functools import partial
from analysis.task_energy import calc_energies_on_dataframe, calc_job_energy_on_job_row, \
    calc_job_energy_on_job_row_single


def get_power_list(start_time, power_csv):
    power_log = pd.read_csv(power_csv)
    power_list = power_log['pkg_current_power'].tolist()
    time_list = power_log['total_time'].tolist()

    if isinstance(start_time, datetime.datetime):
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')

    timestamp_list = [start_time + timedelta(seconds=time) for time in time_list]

    return power_list, timestamp_list

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
    print(df_power_e)
    _calc_job_energy_target_coding = partial(calc_job_energy_on_job_row_single, df_power_e,
                                             lambda x: x['target_coding']['start_time'],
                                             lambda x: x['target_coding']['end_time'])
    df['target_coding_energy'] = df.apply(_calc_job_energy_target_coding, axis=1)

    return df

def get_energy_info(log_file_path, duplicate_count, power_list, time_list):
    with open(log_file_path, 'r') as log_file:
        log_content = log_file.read()
        total_energy = float(log_content.split('Total Energy:')[1].split('J')[0].strip())
        average_power = float(log_content.split('Average Power:')[1].split('W')[0].strip())
        time = float(log_content.split('Time:')[1].split('sec')[0].strip())

        df_energy = test_calc_job_energy(power_list, time_list)
        logger.info(f'df_energy: {df_energy.T}')
        print("==================================================================")
        target_coding_energy = df_energy['target_coding_energy'][0]
        coding_energy = target_coding_energy / duplicate_count

    return total_energy, average_power, time, coding_energy

def measure_command_process(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    logger.debug(process)
    return process

def measure_command_runtime(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    original_working_directory = os.getcwd()
    try:
        powermeter_path = '/home/um20242/rapl-tools'
        os.chdir(powermeter_path)

        start_time = datetime.datetime.now()
        subprocess.run(cmd, encoding="utf-8", shell=True, capture_output=True, text=True)
        end_time = datetime.datetime.now()
    finally:
        os.chdir(original_working_directory)

    logger.info(f'start_time: {start_time}')
    logger.info(f'end_time: {end_time}')
    elapsed_time = end_time - start_time
    elapsed_seconds = elapsed_time.total_seconds()
    logger.info(f'elapsed_time: {elapsed_seconds}')
    return elapsed_seconds

def measure_command_runtime_rapl(cmd, codec, video, coded, qp):
    logger.debug(f'running ffmpeg with command: {cmd}')
    original_working_directory = os.getcwd()
    try:
        powermeter_path = '/home/um20242/rapl-tools'
        os.chdir(powermeter_path)

        start_time = datetime.datetime.now()
        power_meter_result = subprocess.run(cmd, encoding="utf-8", shell=True, capture_output=True, text=True)

        end_time = datetime.datetime.now()
        if power_meter_result.returncode == 0:
            print("AppPowerMeter command executed successfully.")

            source_path = '/home/um20242/rapl-tools/rapl.csv'
            rapl_path = '/home/um20242/quality-energy/videocodec_downsample_4k/rapl_power/'
            power_log = f'{rapl_path}{codec}/{video}_{coded}_crf_{str(qp)}.csv'

            os.makedirs(os.path.dirname(power_log), exist_ok=True)
            column_names = ['pkg_current_power', 'pp0_current_power', 'pp1_current_power', 'dram_current_power', 'total_time']

            if not os.path.exists(power_log):
                pd.DataFrame(columns=column_names).to_csv(power_log, index=False)

            source_df = pd.read_csv(source_path)
            source_df.to_csv(power_log, mode='a', header=False, index=False)

            # shutil.copy(source_path, power_log)
            print(f'File rapl.csv copied to {power_log}')
        else:
            print("AppPowerMeter command failed.")
            print("Error:", power_meter_result.stderr)
    finally:
        os.chdir(original_working_directory)

    return start_time, end_time, power_log

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

def get_raw_yuv_bitrate(pixfmt, video_width, video_height, video_path):
    cmd = f'ffprobe -pixel_format {pixfmt} -video_size {video_width}x{video_height} {video_path}'
    logger.debug(f'running ffmpeg with command: {cmd}')
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.communicate()[1].decode()
    raw_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
    return raw_bitrate

def convert_mkv_to_yuv(video_name, video_path, original_video, pixfmt):
    print('Convert mkv to yuv ' + video_name)
    logger.info(f"Convert mkv to yuv for {video_name}")
    cmd_convert = f'ffmpeg -y -i {video_path + video_name} -c:v rawvideo -pixel_format {pixfmt} {original_video}'
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
        cmd_encode = f'sudo ./AppPowerMeter ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -y -i {original_video} -c:v {codec_name}' \
                     f' -crf {str(qp)} {encoded_video} 1>{encoded_video_log} 2>&1'
    elif codec == 'VVC':
        if pixfmt == 'yuv420p10le':
            pixfmt_c = 'yuv420_10'
        else:
            pixfmt_c = 'yuv420'
        encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.bin'
        cmd_encode = f'vvencapp -s {video_width}x{video_height} -r {framerate} -c {pixfmt_c} -i {original_video} --preset medium -q {str(qp)} -o {encoded_video} 1>{encoded_video_log} 2>&1'

    return cmd_encode, encoded_video, encoded_video_log

def get_encoded_bitrate(encoded_video):
    cmd = f'ffprobe {encoded_video}'
    logger.debug(f'running ffmpeg with command: {cmd}')
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = res.communicate()[1].decode()
    encoded_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
    logger.info(f'encoded_bitrate: {encoded_bitrate}')

    return encoded_bitrate

def calculate_psnr(codec_path, video, qp, framerate, video_width, video_height, pixfmt, original_video, decoded_video):
    psnr_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.csv'
    cmd_psnr = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video}' \
               f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {decoded_video} -lavfi psnr=stats_file={psnr_log} -f null -'
    logger.debug(f'running ffmpeg with command: {cmd_psnr}')
    res2 = subprocess.Popen(cmd_psnr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output2 = res2.communicate()[1].decode()
    psnr = get_info(output2, r'(?:average:)\d+\.?\d*', "average:")
    logger.info(f'psnr: {psnr}')

    return psnr

def decoding_video_output(codec, video, qp, decode_path, encoded_video):
    print(f'Start {codec} Decode for {video} at crf {str(qp)}')
    logger.info(f"Start {codec} Decode for {video} at crf {str(qp)}")

    decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
    decoded_video_log = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.txt'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        cmd_decode = f'ffmpeg -i {encoded_video} -y -f rawvideo {decode_video} 1>{decoded_video_log} 2>&1' #-f: not allow to put in the standard output.
    elif codec == 'VVC':
        cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'
    return cmd_decode, decode_video

def decoding_video_nooutput(codec, video, qp, decode_path, encoded_video):
    print(f'Start {codec} Decode for {video} at crf {str(qp)}')
    logger.info(f"Start {codec} Decode for {video} at crf {str(qp)}")

    decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
    decoded_video_log = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.txt'
    if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
        cmd_decode = f'sudo ./AppPowerMeter ffmpeg -i {encoded_video} -benchmark -y -f null - 1>{decoded_video_log} 2>&1' #-f: not allow to put in the standard output.
    elif codec == 'VVC':
        cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'
    return cmd_decode, decode_video, decoded_video_log

def compute_vmaf(video, qp, vmaf_path, codec, video_width, video_height, framerate, pixfmt, original_video,
                 decode_video):
    print('Start VMAF computation for ' + video + ' at crf' + str(qp))
    logger.info(f"Start VMAF computation for {video} at crf {str(qp)}")

    vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(qp)}_upsample_2160p.csv'
    cmd_vmaf = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video}' \
               f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video}' \
               f' -lavfi "[0:v]setpts=PTS-STARTPTS[reference]; [1:v]setpts=PTS-STARTPTS[distorted]; [distorted][reference]' \
               f'libvmaf=log_fmt=xml:log_path={vmaf_name}:model_path=../model/vmaf_4k_v0.6.1.json:n_threads=4" ' \
               f'-f null -'

    logger.debug(f'running ffmpeg with command: {cmd_vmaf}')
    subprocess.run(cmd_vmaf, encoding="utf-8", shell=True)

    # read vmaf for decoded video
    vmaf_csv = pd.read_csv(vmaf_name)
    vmaf_line = vmaf_csv.iloc[[-4]].to_string()  # .values.tolist()
    vmaf = get_info(vmaf_line, r'(?:" mean=")\d+\.?\d*', '" mean="')
    logger.info(f'vmaf: {vmaf}')

    return vmaf

def downscale_video(original_video, ugcdata_down_path, video, video_width, video_height, framerate, pixfmt):
    logger.info('Start Downsample to 1080p/720p for ' + original_video)

    downsample_video_1080 = f'{ugcdata_down_path}{video}_downsample_1080p.yuv'
    cmd_downscale_1080 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=1920:1080:flags=lanczos -s:v 1920x1080 -r {framerate} -pix_fmt {pixfmt} {downsample_video_1080}'
    logger.debug(f'running ffmpeg with command: {cmd_downscale_1080}')
    subprocess.run(cmd_downscale_1080, encoding="utf-8", shell=True)

    downsample_video_720 = f'{ugcdata_down_path}{video}_downsample_720p.yuv'
    cmd_downscale_720 = f'ffmpeg -s:v {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -vf scale=1280:720:flags=lanczos -s:v 1280x720 -r {framerate} -pix_fmt {pixfmt} {downsample_video_720}'
    logger.debug(f'running ffmpeg with command: {cmd_downscale_720}')
    subprocess.run(cmd_downscale_720, encoding="utf-8", shell=True)

    return downsample_video_1080, downsample_video_720

def upscale_video(downsample_video, qp, upscale_path, codec, width, height, framerate, pixfmt, decode_video):
    logger.info('Start Upsample to 2160p for ' + downsample_video + ' at crf' + str(qp))

    upsample_video_yuv = f'{upscale_path}{codec}/{downsample_video}_decoded_crf_{str(qp)}_upsample_2160p.yuv'
    cmd_upscale = f'ffmpeg -s:v {width}x{height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video} -vf scale=3840:2160:flags=lanczos -s:v 3840x2160 -r {framerate} -pix_fmt {pixfmt} {upsample_video_yuv}'
    subprocess.run(cmd_upscale, encoding="utf-8", shell=True)

    return upsample_video_yuv

def get_video_frame_count(yuv_filename, width, height):
    frame_size = width * height * 3 // 2
    file_size = os.path.getsize(yuv_filename)
    frame_count = file_size // frame_size
    return frame_count

if __name__ == '__main__':
    # logging config
    with open('logging_4k_rapl.yml', 'r') as file_logging:
        dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
    logging.config.dictConfig(dict_conf)
    logger = logging.getLogger('default')
    logger.info("\n ==================================================================")
    logger.info('This is a log info for video codecs')

    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_2160P_metadata_downsample.csv")

    ugcdata_ori_path = '/home/um20242/quality-energy/ugc-dataset/2160P/'
    ugcdata_duplicate_path = '/home/um20242/quality-energy/videocodec_4k/duplicate/'
    encode_path = '/home/um20242/quality-energy/videocodec_4k/encoded/'
    decode_path = '/home/um20242/quality-energy/videocodec_4k/decoded/'
    ffmpeg_path = '/home/um20242/quality-energy/videocodec_4k/ffmpeg/'
    original_path = '/home/um20242/quality-energy/videocodec_4k/input/'
    vmaf_path = '/home/um20242/quality-energy/videocodec_4k/vmaf/'

    codec = 'x264'
    codec_path = f'{ffmpeg_path}{codec}/'
    if codec == 'x265':
        codec_name = 'libx265'
        # qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
        qp_level = [10, 20, 30, 40, 50]
    elif codec == 'x264':
        codec_name = 'libx264'
        # qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
        qp_level = [10, 20, 30, 40, 50]
    elif codec == 'VP9':
        codec_name = 'libvpx-vp9'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
    elif codec == 'SVT-AV1':
        codec_name = 'libsvtav1'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]

    for i in range(len(ugcdata)):
        df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framerate',
                                           'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP',
                                           'encoding_elapsed_time', 'decoding_elapsed_time',
                                           'duplicate_count', 'duplicate_bitrate_rawvideo (kb/s)',
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
        encoding_elapsed_time_list = []
        decoding_elapsed_time_list = []

        # compute the energy
        duplicate_count_list = []
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
        df_encoding_power = pd.DataFrame(
            columns=['vid', 'time', 'power'])
        df_decoding_power = pd.DataFrame(
            columns=['vid', 'time', 'power'])
        total_encoding_power_list = []
        total_encoding_time_list = []
        total_decoding_power_list = []
        total_decoding_time_list = []

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

        print(f'--------------------Run the process without downsampling for {codec}------------------------')
        for qp in qp_level:
            vid_list.append(video)
            cate_list.append(category)
            res_list.append(resolution)
            width_list.append(video_width)
            height_list.append(video_height)
            pix_list.append(pixfmt)
            fps_list.append(framerate)
            bitrate_raw_list.append(raw_bitrate)
            qp_list.append(qp)

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video, encoded_video_log = encoding_video(codec, video, qp, framerate, video_width, video_height, pixfmt, original_video, encode_path)
            encoding_elapsed_time = measure_command_runtime(cmd_encode)
            encoding_elapsed_time_list.append(encoding_elapsed_time)

            # ------------------------read bitrate for encoded video------------------------
            encoded_bitrate = get_encoded_bitrate(encoded_video)
            bitrate_encoded_list.append(encoded_bitrate)

            # --------------------Start Decode------------------------
            cmd_decode, decode_video = decoding_video_output(codec, video, qp, decode_path, encoded_video)
            decoding_elapsed_time = measure_command_runtime(cmd_decode)
            decoding_elapsed_time_list.append(decoding_elapsed_time)

            # --------------------Trim the video------------------------
            original_frame_count = get_video_frame_count(original_video, video_width, video_height)
            compressed_frame_count = get_video_frame_count(decode_video, video_width, video_height)

            logger.info(f'original_frame_count: {original_frame_count}')
            logger.info(f'compressed_frame_count: {compressed_frame_count}')
            logger.info('---------------------------------------------')
            if original_frame_count != compressed_frame_count:
                compressed_yuv = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}_tr.yuv'
                cmd_trim = f'ffmpeg -s {video_width}x{video_height} -i {decode_video} -vf select="between(n\,1\,{compressed_frame_count}),setpts=PTS-STARTPTS" {compressed_yuv}'
                print(cmd_trim)
                subprocess.run(cmd_trim, encoding="utf-8", shell=True)
                os.remove(decode_video)
            else:
                compressed_yuv = decode_video

            # ------------------------read psnr for encoded video------------------------
            psnr = calculate_psnr(codec_path, video, qp, framerate, video_width, video_height, pixfmt, original_video, compressed_yuv)
            psnr_list.append(psnr)

            # --------------------VMAF computaion------------------------
            vmaf = compute_vmaf(video, qp, vmaf_path, codec, video_width, video_height, framerate, pixfmt, original_video, compressed_yuv)
            vmaf_list.append(vmaf)

            # remove input and decoded files for saving space
            # os.remove(encoded_video)
            # os.remove(decode_video)
            os.remove(compressed_yuv)
        os.remove(original_video)

        # metrics
        df_metrics['vid'] = vid_list
        df_metrics['category'] = cate_list
        df_metrics['resolution'] = res_list
        df_metrics['width'] = width_list
        df_metrics['height'] = height_list
        df_metrics['pixfmt'] = pix_list
        df_metrics['framerate'] = fps_list
        df_metrics['bitrate_rawvideo (kb/s)'] = bitrate_raw_list
        df_metrics['bitrate_encoded (kb/s)'] = bitrate_encoded_list
        df_metrics['PSNR'] = psnr_list
        df_metrics['VMAF'] = vmaf_list
        df_metrics['QP'] = qp_list
        df_metrics['encoding_elapsed_time'] = encoding_elapsed_time_list
        df_metrics['decoding_elapsed_time'] = decoding_elapsed_time_list

        print(df_metrics)
        metrics_name = f'../videocodec_4k/YOUTUBE_UGC_2160P_nodownsample_{codec}_metrics_{video}.csv'
        df_metrics.to_csv(metrics_name, index=None)




        # --------------------Calcultate energy------------------------
        print(f'--------------------Run the energy measurement process for {codec}------------------------')
        logger.info(f'------------------------------------------------------------------------------------')
        logger.info(f"Run the energy measurement process for {codec}")
        video_name = f'{video}.mkv'
        original_video_yuv = f'{original_path}{video}.yuv'

        # --------------------Convert mkv to yuv------------------------
        convert_mkv_to_yuv(video_name, ugcdata_ori_path, original_video, pixfmt)

        print(f'--------------------Run the energy measurement process without downsampling for {codec}------------------------')
        original_video_list = [f'{video}']
        original_width_list = [3840]
        original_height_list = [2160]
        result_list = [(original_video, qp, original_width, original_height) for
                       original_video, original_width, original_height in
                       zip(original_video_list, original_width_list, original_height_list) for qp in qp_level]

        for index, (original_video, qp, original_width, original_height) in enumerate(result_list):
            logger.info(f"Index: {index}, original_video: {original_video}, qp: {qp}, original_width: {original_width}, original_height: {original_height}")

            # elapsed_time = decoding_elapsed_time_list[index]
            duplicate_count = 1
            duplicate_count_list.append(duplicate_count)
            # logger.info(f"decoding_elapsed_time: {elapsed_time}, duplicate_count: {duplicate_count}")

            duplicate_path = ugcdata_duplicate_path
            original_duplicate = f'{original_video}_duplicate'
            original_duplicate_yuv = original_video_yuv

            # read bitrate for raw duplicate video
            raw_bitrate_duplicate = get_raw_yuv_bitrate(pixfmt, original_width, original_height, original_duplicate_yuv)
            duplicate_bitrate_raw_list.append(raw_bitrate_duplicate)

            # --------------------Start Encode------------------------
            cmd_encode, encoded_video, encoded_video_log = encoding_video(codec, original_duplicate, qp, framerate, original_width,
                                                       original_height, pixfmt, original_duplicate_yuv, encode_path)

            ## ------------------------get power log for encoding process------------------------
            logger.info(f'get power log for encoding process')
            start_time_encode, end_time_encode, encode_power_log = measure_command_runtime_rapl(cmd_encode, codec, encoded_video, 'encoded', qp)
            encoding_power_list, encoding_time_list = get_power_list(start_time_encode, encode_power_log)

            logger.info(f'start_time_encode: {start_time_encode}')
            logger.info(f'end_time_encode: {end_time_encode}')
            start_time_encode_list.append(start_time_encode)
            end_time_encode_list.append(end_time_encode)

            print_encode_energy, average_encode_power, encode_duration, encode_energy = get_energy_info(encoded_video_log, duplicate_count, encoding_power_list, encoding_time_list)
            logger.info(f'print_encode_energy: {print_encode_energy} J')
            logger.info(f'average_encode_power: {average_encode_power} W')
            logger.info(f'encode_duration: {encode_duration} sec')
            logger.info(f'encode_energy: {encode_energy} J')
            count_encode_list.append(1)
            encode_energy_list.append(encode_energy)

            # --------------------Start Decode------------------------
            cmd_decode, decode_video, decoded_video_log = decoding_video_nooutput(codec, original_duplicate, qp, decode_path, encoded_video)

            ## ------------------------get power log for decoding process------------------------
            logger.info(f'get power log for decoding process')
            start_time_decode, end_time_decode, decode_power_log = measure_command_runtime_rapl(cmd_decode, codec, decode_video, 'decoded', qp)
            decoding_power_list, decoding_time_list = get_power_list(start_time_decode, decode_power_log)

            logger.info(f'start_time_decode: {start_time_decode}')
            logger.info(f'end_time_decode: {end_time_decode}')
            start_time_decode_list.append(start_time_decode)
            end_time_decode_list.append(end_time_decode)

            print_decode_energy, average_decode_power, decode_duration, decode_energy = get_energy_info(decoded_video_log, duplicate_count, decoding_power_list, decoding_time_list)
            logger.info(f'print_decode_energy: {print_decode_energy} J')
            logger.info(f'average_decode_power: {average_decode_power} W')
            logger.info(f'decode_duration: {decode_duration} sec')
            logger.info(f'decode_energy: {decode_energy} J')
            count_decode_list.append(1)
            decode_energy_list.append(decode_energy)

            total_energy = encode_energy + decode_energy
            total_energy_list.append(total_energy)

            # keep power log
            total_encoding_power_list.append(encoding_power_list)
            total_encoding_time_list.append(encoding_time_list)
            total_decoding_power_list.append(decoding_power_list)
            total_decoding_time_list.append(decoding_time_list)

            # remove input and decoded files for saving space
            # os.remove(encoded_video)
            # os.remove(decode_video)
        os.remove(original_video_yuv)


        # energy log
        df_metrics['duplicate_count'] = duplicate_count_list
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
        energy_name = f'../metrics/rapl_energy/{codec}/YOUTUBE_UGC_2160P_nodownsample_{codec}_metrics_timestamp_duplicate_energy_{video}.csv'
        df_metrics.to_csv(energy_name, index=None)

        logger.info('Finish')

        # keep power log
        df_encoding_power['vid'] = vid_list
        df_encoding_power['power'] = total_encoding_power_list
        df_encoding_power['time'] = total_encoding_time_list
        df_encoding_power_name = f'../metrics/rapl_energy_log/{codec}/YOUTUBE_UGC_2160P_nodownsample_{codec}_duplicate_encoding_power_log_{video}.csv'
        df_encoding_power.to_csv(df_encoding_power_name, index=None)

        df_decoding_power['vid'] = vid_list
        df_decoding_power['power'] = total_decoding_power_list
        df_decoding_power['time'] = total_decoding_time_list
        df_decoding_power_name = f'../metrics/rapl_energy_log/{codec}/YOUTUBE_UGC_2160P_nodownsample_{codec}_duplicate_decoding_power_log_{video}.csv'
        df_decoding_power.to_csv(df_decoding_power_name, index=None)
