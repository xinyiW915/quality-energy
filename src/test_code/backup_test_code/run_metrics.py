import pandas as pd
import subprocess
import re
import os

def get_last_line(filename):
    """
    get last line of a file
    :param filename: file name
    :return: last line or None for empty file
    """
    try:
        filesize = os.path.getsize(filename)
        if filesize == 0:
            return None
        else:
            with open(filename, 'rb') as fp: # to use seek from end, must use mode 'rb'
                offset = -8                 # initialize offset
                while -offset < filesize:   # offset cannot exceed file size
                    fp.seek(offset, 2)      # read # offset chars from eof(represent by number '2')
                    lines = fp.readlines()  # read from fp to eof
                    if len(lines) >= 2:     # if contains at least 2 lines
                        return lines[-1]    # then last line is totally included
                    else:
                        offset *= 2         # enlarge offset
                fp.seek(0)
                lines = fp.readlines()
                return lines[-1]
    except FileNotFoundError:
        print(filename + ' not found!')
        return None

def get_info(output, patt, info_name):
    # output_text = re.findall(findtext, output) #"bitrate:+..+kb/s"  "PSNR+......+"
    pattern = re.compile(patt)
    output_text = pattern.findall(output)
    info = "".join(output_text)
    info = info.replace(info_name, "")
    return info

if __name__ == '__main__':
    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_1080P_metadata.csv")
    print(ugcdata)

    ugcdata_path = '../ugc-dataset/'
    decode_path = '../videocodec/decoded/'
    encode_path = '../videocodec/encoded/'
    ffmpeg_path = '../videocodec/ffmpeg/'
    original_path = '../videocodec/input/'
    vmaf_path = '../videocodec/vmaf/'

    codec = 'x265'
    codec_path = f'{ffmpeg_path}{codec}/'
    if codec == 'x265':
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
    elif codec == 'x264':
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
    elif codec == 'VP9':
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
    elif codec == 'SVT-AV1':
        qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
    elif codec == 'VVC':
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]

    df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framrate', 'bitrate_rawvideo (kb/s)', 'bitrate_hevc (kb/s)', 'PSNR', 'VMAF', 'QP'])

    vid_list = []
    cate_list = []
    res_list = []
    width_list = []
    height_list = []
    pix_list = []
    fps_list = []
    bitrate_raw = []
    bitrate_hevc = []
    psnr_list = []
    vmaf_list = []
    qp_list = []

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
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = res.communicate()[1].decode()
        # print(output)
        raw_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")

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

            # read bitrate for encoded video
            encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.mp4'
            cmd1 = f'ffprobe {encoded_video}'
            res1 = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output1 = res1.communicate()[1].decode()
            encoded_bitrate = get_info(output1, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
            bitrate_hevc.append(encoded_bitrate)

            # read psnr for encoded video
            codec_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.txt'
            last_txt = get_last_line(codec_log).decode()
            psnr = get_info(last_txt, r'(?:PSNR: )\d+\.?\d*', "PSNR: ")
            psnr_list.append(psnr)

            # read vmaf for decoded video
            vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(qp)}.csv'
            vmaf_csv = pd.read_csv(vmaf_name)
            vmaf_line = vmaf_csv.iloc[[-4]].to_string() # .values.tolist()
            vmaf = get_info(vmaf_line, r'(?:" mean=")\d+\.?\d*', '" mean="')
            vmaf_list.append(vmaf)


    df_metrics['vid'] = vid_list
    df_metrics['category'] = cate_list
    df_metrics['resolution'] = res_list
    df_metrics['width'] = width_list
    df_metrics['height'] = height_list
    df_metrics['pixfmt']= pix_list
    df_metrics['framrate'] = fps_list
    df_metrics['bitrate_rawvideo (kb/s)'] = bitrate_raw
    df_metrics['bitrate_hevc (kb/s)'] = bitrate_hevc
    df_metrics['PSNR'] = psnr_list
    df_metrics['VMAF'] = vmaf_list
    df_metrics['QP'] = qp_list

    print(df_metrics)
    metrics_name = f'../metrics/YOUTUBE_UGC_1080P_{codec}_metrics.csv'
    df_metrics.to_csv(metrics_name, index=None)