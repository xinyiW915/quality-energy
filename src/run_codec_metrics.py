import pandas as pd
import subprocess
import re
import os

def get_info(output, patt, info_name):
    # output_text = re.findall(findtext, output) #"bitrate:+..+kb/s"  "PSNR+......+"
    pattern = re.compile(patt)
    output_text = pattern.findall(output)
    info = "".join(output_text)
    info = info.replace(info_name, "")
    return info

if __name__ == '__main__':
    ugcdata = pd.read_csv("../metadata/YOUTUBE_UGC_1080P_metadata.csv")
    # print(ugcdata)

    ugcdata_path = '../ugc-dataset/'
    decode_path = '../videocodec/decoded/'
    encode_path = '../videocodec/encoded/'
    ffmpeg_path = '../videocodec/ffmpeg/'
    original_path = '../videocodec/input/'
    vmaf_path = '../videocodec/vmaf/'

    codec = 'VVC'
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
    elif codec == 'VVC':
        qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]

    df_metrics = pd.DataFrame(columns=['vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framrate', 'bitrate_rawvideo (kb/s)',
                                       'bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP'])

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
        cmd = f'ffmpeg {raw_video}'
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = res.communicate()[1].decode()
        # print(output)
        raw_bitrate = get_info(output, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
        # print(raw_bitrate)

        print(f'--------------------Run the process for {codec}------------------------')
        video_name = f'{video}.mkv'
        original_video = f'{original_path}{video}.yuv'

        # --------------------Convert mkv to yuv------------------------
        print('Convert mkv to yuv ' + video_name)
        cmd_convert = f'ffmpeg -y -i {ugcdata_path + video_name} -c:v rawvideo -pixel_format {pixfmt} {original_video}'
        print(cmd_convert)
        subprocess.run(cmd_convert, encoding="utf-8", shell=True)

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

            if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
                if codec == 'VP9':
                    encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.webm'
                else:
                    encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.mp4'
                cmd_encode = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -c:v {codec_name}' \
                             f' -crf {str(qp)} {encoded_video}'
            elif codec == 'VVC':
                if pixfmt == 'yuv420p10le':
                    pixfmt_c = 'yuv420_10'
                else:
                    pixfmt_c = 'yuv420'
                encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.bin'
                vvc_log = f'{codec_path}{video}_EncodeResult_fps{str(framerate)}_crf_{str(qp)}.txt'
                # cmd_encode = f'vvencapp -s {video_width}x{video_height} -r {framerate} -c {pixfmt_c} -i {original_video} --preset medium -q {str(qp)} -o {encoded_video}'
                cmd_encode = f'vvencFFapp -i {original_video} --Size {video_width}x{video_height} -fr {framerate} -b {encoded_video} -g 16 -ip 64 --QP {str(qp)} --InputChromaFormat 420 >> {vvc_log}'

            print(cmd_encode)
            subprocess.run(cmd_encode, encoding="utf-8", shell=True)

            # read bitrate for encoded video
            cmd1 = f'ffmpeg {encoded_video}'
            res1 = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output1 = res1.communicate()[1].decode()
            # print(output1)
            encoded_bitrate = get_info(output1, r'(?:bitrate: )\d+\.?\d*', "bitrate: ")
            # print(encoded_bitrate)
            bitrate_encoded.append(encoded_bitrate)

            # read psnr for encoded video
            psnr_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(qp)}.csv'
            cmd_psnr = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video} -i {encoded_video} -lavfi psnr=stats_file={psnr_log} -f null -'
            print(cmd_psnr)
            res2 = subprocess.Popen(cmd_psnr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output2 = res2.communicate()[1].decode()
            print(output2)
            psnr = get_info(output2, r'(?:average:)\d+\.?\d*', "average:")
            print(psnr)
            psnr_list.append(psnr)

            # --------------------Start Decode------------------------
            decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(qp)}.yuv'

            print(f'Start {codec} Decode for ' + video_name + ' at crf' + str(qp))

            if codec == 'x265' or codec == 'x264' or codec == 'VP9' or codec == 'SVT-AV1':
                cmd_decode = f'ffmpeg -i {encoded_video} -y {decode_video}'
            elif codec == 'VVC':
                cmd_decode = f'vvdecapp -b {encoded_video} -o {decode_video}'

            print(cmd_decode)
            subprocess.run(cmd_decode, encoding="utf-8", shell=True)

            # --------------------VMAF computaion------------------------
            vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(qp)}.csv'

            print('Start VMAF computation for ' + video_name + ' at crf' + str(qp))
            cmd_vmaf = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {original_video}' \
                       f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video}' \
                       f' -lavfi "[0:v]setpts=PTS-STARTPTS[reference]; [1:v]setpts=PTS-STARTPTS[distorted]; [distorted][reference]' \
                       f'libvmaf=log_fmt=xml:log_path={vmaf_name}:model_path=../model/vmaf_v0.6.1.json:n_threads=4" ' \
                       f'-f null -'

            print(cmd_vmaf)
            subprocess.run(cmd_vmaf, encoding="utf-8", shell=True)

            # read vmaf for decoded video
            vmaf_csv = pd.read_csv(vmaf_name)
            vmaf_line = vmaf_csv.iloc[[-4]].to_string() # .values.tolist()
            vmaf = get_info(vmaf_line, r'(?:" mean=")\d+\.?\d*', '" mean="')
            vmaf_list.append(vmaf)

            # remove input and decoded files for saving space
            os.remove(encoded_video)
            os.remove(decode_video)
        os.remove(original_video)

    df_metrics['vid'] = vid_list
    df_metrics['category'] = cate_list
    df_metrics['resolution'] = res_list
    df_metrics['width'] = width_list
    df_metrics['height'] = height_list
    df_metrics['pixfmt']= pix_list
    df_metrics['framrate'] = fps_list
    df_metrics['bitrate_rawvideo (kb/s)'] = bitrate_raw
    df_metrics['bitrate_encoded (kb/s)'] = bitrate_encoded
    df_metrics['PSNR'] = psnr_list
    df_metrics['VMAF'] = vmaf_list
    df_metrics['QP'] = qp_list

    print(df_metrics)
    metrics_name = f'../metrics/YOUTUBE_UGC_1080P_{codec}_metrics.csv'
    df_metrics.to_csv(metrics_name, index=None)
