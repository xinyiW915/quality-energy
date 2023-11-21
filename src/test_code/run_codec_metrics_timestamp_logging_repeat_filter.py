import subprocess
import re
import os

import pandas as pd
import datetime
import logging.config
import logging
import yaml
import shlex


def get_info(output, patt, info_name):
    # output_text = re.findall(findtext, output) #"bitrate:+..+kb/s"  "PSNR+......+"
    pattern = re.compile(patt)
    output_text = pattern.findall(output)
    info = "".join(output_text)
    info = info.replace(info_name, "")
    return info

def measure_command_process(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    print(process)
    return process

def measure_command_runtime(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    start_time = datetime.datetime.now()
    subprocess.run(cmd, encoding="utf-8", shell=True)
    end_time = datetime.datetime.now()
    return start_time, end_time

def measure_command_runtime_filter(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    # repeat process
    count_repeat = 10  # 1 time for just consider the encoding time first
    start_time = datetime.datetime.now()
    for i in range(count_repeat):
        subprocess.run(cmd, encoding="utf-8", shell=True)
        print(str(i+1) + 'times: ' + cmd)
    end_time = datetime.datetime.now()
    return start_time, end_time

if __name__ == '__main__':
    # logging config
    with open('logging.yml', 'r') as file_logging:
        dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
    logging.config.dictConfig(dict_conf)
    logger = logging.getLogger('default')
    logger.info('This is a log info for video codecs')

    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_1080P_metadata.csv")

    ugcdata_path = '../ugc-dataset/'
    decode_path = '../videocodec/decoded/'
    encode_path = '../videocodec/encoded/'
    ffmpeg_path = '../videocodec/ffmpeg/'
    original_path = '../videocodec/input/'
    vmaf_path = '../videocodec/vmaf/'
    energy_path = '../videocodec/energy_logs/'

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
        codec_name = 'libsvtav1'  # 'libaom-av1' #'libsvtav1'
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
    elif codec == 'VVC':
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]

    df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framrate',
                                       'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP',
                                       'start_time_encode', 'end_time_encode', 'start_time_decode', 'end_time_decode'])
    vid_list = []
    cate_list = []
    res_list = []
    width_list = []
    height_list = []
    pix_list = []
    fps_list = []
    bitrate_raw = []
    bitrate_encoded = []
    psnr_list = []
    vmaf_list = []
    qp_list = []
    start_time_encode_list = []
    end_time_encode_list = []
    start_time_decode_list = []
    end_time_decode_list = []

    for i in range(len(ugcdata)):

        video = ugcdata['vid'][i]
        category = ugcdata['category'][i]
        resolution = ugcdata['resolution'][i]
        video_width = ugcdata['width'][i]
        video_height = ugcdata['height'][i]
        pixfmt = ugcdata['pixfmt'][i]
        framerate = ugcdata['framerate'][i]

        # read bitrate for raw video
        raw_video = f'{ugcdata_path}{video}.mkv'
        cmd = f'ffprobe {raw_video}'
        logger.debug(f'running ffmpeg with command: {cmd}')
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = res.communicate()[1].decode()
        raw_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")


        print(f'--------------------Run the process for {codec}------------------------')
        logger.info(f"Starting with encoder {codec}")
        video_name = f'{video}.mkv'
        orignial_video = f'{original_path}{video}.yuv'

        # --------------------Convert mkv to yuv------------------------
        print('Convert mkv to yuv ' + video_name)
        logger.info(f"Convert mkv to yuv for {video_name}")
        cmd_convert = f'ffmpeg -y -i {ugcdata_path + video_name} -pix_fmt yuv420p -vsync 0 {orignial_video}'
        process_convert = measure_command_process(cmd_convert)
        if process_convert.returncode != 0:
            logger.error('error: process.returncode != 0')
            raise ValueError(process_convert.stdout)

        for qp in qp_level:
            vid_list.append(video)
            cate_list.append(category)
            res_list.append(resolution)
            width_list.append(video_width)
            height_list.append(video_height)
            pix_list.append(pixfmt)
            fps_list.append(framerate)
            bitrate_raw.append(raw_bitrate)
            qp_list.append(qp)

            # --------------------Start Encode------------------------
            print(f'Start {codec} Encode for ' + video_name + ' at crf' + str(qp) + ', fps: ' + str(framerate))
            logger.info(f"Start {codec} Encode for {video_name} at crf {str(qp)}, fps: {str(framerate)}")

            encoded_video_log = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.txt'
            if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
                if codec == 'VP9':
                    encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.webm'
                else:
                    encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.mp4'
                cmd_encode = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -y -i {orignial_video} -c:v {codec_name}' \
                             f' -crf {str(qp)} {encoded_video} 1>{encoded_video_log} 2>&1'
            elif codec == 'VVC':
                if pixfmt == 'yuv420p10le':
                    pixfmt_c = 'yuv420_10'
                else:
                    pixfmt_c = 'yuv420'
                encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.bin'
                vvc_log = f'{codec_path}{video}_EncodeResult_fps{str(framerate)}_crf_{str(qp)}.txt'
                cmd_encode = f'vvencapp -s {video_width}x{video_height} -r {framerate} -c {pixfmt_c} -i {orignial_video} --preset medium -q {str(qp)} -o {encoded_video} 1>{encoded_video_log} 2>&1'
                # cmd_encode = f'vvencFFapp -i {orignial_video} --Size {video_width}x{video_height} -fr {framerate} -b {encoded_video} -g 16 -ip 64 --QP {str(qp)} --InputChromaFormat 420 >> {vvc_log}'

            start_time_encode, end_time_encode= measure_command_runtime_filter(cmd_encode)
            print(f'start_time_encode: {start_time_encode}')
            print(f'end_time_encode: {end_time_encode}')

            # ------------------------read bitrate for encoded video------------------------
            cmd1 = f'ffprobe {encoded_video}'
            logger.debug(f'running ffmpeg with command: {cmd1}')
            res1 = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output1 = res1.communicate()[1].decode()
            encoded_bitrate = get_info(output1, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
            bitrate_encoded.append(encoded_bitrate)

            # ------------------------read psnr for encoded video------------------------
            psnr_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.csv'
            cmd_psnr = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {orignial_video} -i {encoded_video} -lavfi psnr=stats_file={psnr_log} -f null -'
            logger.debug(f'running ffmpeg with command: {cmd_psnr}')
            res2 = subprocess.Popen(cmd_psnr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output2 = res2.communicate()[1].decode()
            psnr = get_info(output2, r'(?:average:)\d+\.?\d*', "average:")
            psnr_list.append(psnr)

            # --------------------Start Decode------------------------
            print(f'Start {codec} Decode for ' + video_name + ' at crf' + str(qp))
            logger.info(f"Start {codec} Decode for {video_name} at crf {str(qp)}")

            decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'
            if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
                cmd_decode = f'ffmpeg -i {encoded_video} -y {decode_video}'
            elif codec == 'VVC':
                cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'

            #discard the decoding time energy test for now
            start_time_decode, end_time_decode= measure_command_runtime_filter(cmd_decode)
            print(f'start_time_decode: {start_time_decode}')
            print(f'end_time_decode: {end_time_decode}')

            # --------------------VMAF computaion------------------------
            print('Start VMAF computation for ' + video_name + ' at crf' + str(qp))
            logger.info(f"Start VMAF computation for {video_name} at crf {str(qp)}")

            vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(qp)}.csv'
            cmd_vmaf = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {orignial_video}' \
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
            vmaf_list.append(vmaf)

            # save timestamp
            # energy_name = f'{energy_path}{codec}/{video}_timestamp_fps{str(framerate)}_crf_{str(qp)}.csv'
            # df_energy = record_job_timestamp(start_time_encode, end_time_encode, start_time_decode, end_time_decode,
            #                                  count_decode)
            # df_energy.to_csv(energy_name, index=None)

            start_time_encode_list.append(start_time_encode)
            end_time_encode_list.append(end_time_encode)
            start_time_decode_list.append(start_time_decode)
            end_time_decode_list.append(end_time_decode)

            # remove input and decoded files for saving space
            os.remove(encoded_video)
            os.remove(decode_video)
        os.remove(orignial_video)

    df_metrics['vid'] = vid_list
    df_metrics['category'] = cate_list
    df_metrics['resolution'] = res_list
    df_metrics['width'] = width_list
    df_metrics['height'] = height_list
    df_metrics['pixfmt'] = pix_list
    df_metrics['framrate'] = fps_list
    df_metrics['bitrate_rawvideo (kb/s)'] = bitrate_raw
    df_metrics['bitrate_encoded (kb/s)'] = bitrate_encoded
    df_metrics['PSNR'] = psnr_list
    df_metrics['VMAF'] = vmaf_list
    df_metrics['QP'] = qp_list
    df_metrics['start_time_encode'] = start_time_encode_list
    df_metrics['end_time_encode'] = end_time_encode_list
    df_metrics['start_time_decode'] = start_time_decode_list
    df_metrics['end_time_decode'] = end_time_decode_list

    print(df_metrics)
    metrics_name = f'../metrics/energy_log/YOUTUBE_UGC_1080P_{codec}_metrics_timestamp_filter.csv'
    df_metrics.to_csv(metrics_name, index=None)

    logger.info('Finish')


