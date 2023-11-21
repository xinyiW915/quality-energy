import pandas as pd
import os
import subprocess

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
    codec_name = 'libx265'
    qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
elif codec == 'x264':
    codec_name = 'libx264'
    qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]
elif codec == 'VP9':
    codec_name = 'libvpx-vp9'
    qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
elif codec == 'SVT-AV1':
    codec_name = 'libaom-av1'
    qp_level = [12, 18, 24, 30, 36, 42, 48, 54, 60]
elif codec == 'VVC':
    # codec_name =
    qp_level = [10, 15, 20, 25, 30, 35, 40, 45, 50]


for i in range(len(ugcdata)):

    video = ugcdata['vid'][i]
    video_width = ugcdata['width'][i]
    video_height = ugcdata['height'][i]
    pixfmt = ugcdata['pixfmt'][i]
    framerate = ugcdata['framerate'][i]

    print(f'--------------------Run the process for {codec}------------------------')
    video_name = f'{video}.mkv'
    orignial_video = f'{original_path}{video}.yuv'

    # --------------------Convert mkv to yuv------------------------
    print('Convert mkv to yuv ' + video_name)
    cmd_convert = f'ffmpeg -loglevel error -y -i {ugcdata_path + video_name} -pix_fmt yuv420p -vsync 0 {orignial_video}'
    print(cmd_convert)
    subprocess.run(cmd_convert, encoding="utf-8", shell=True)

    # --------------------Start Encode------------------------
    for crf in qp_level:
        codec_log = f'{codec_path}{video}_encoded_fps{str(framerate)}_crf_{str(crf)}.txt'
        encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(crf)}.mp4'

        print(f'Start {codec} Encode for ' + video_name + ' at crf' + str(crf) + ', fps: ' + str(framerate))

        if codec == 'x265' or codec == 'x264':
            cmd_encode = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {orignial_video} -c:v {codec_name}' \
                         f' -preset veryfast -crf {str(crf)} -psnr {encoded_video}' \
                         f' > {codec_log} 2>&1'
        elif codec == 'VP9':
            cmd_encode = f'ffmpeg -s {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {orignial_video} -c:v {codec_name}' \
                         f' -row-mt 1 -crf {str(crf)} -b:v 0 {encoded_video}'

        print(cmd_encode)
        subprocess.run(cmd_encode, encoding="utf-8", shell=True)

    # --------------------Start Decode------------------------
    for crf in qp_level:
        encoded_video = f'{encode_path}{codec}/{video}_encoded_fps{str(framerate)}_crf_{str(crf)}.mp4'
        decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(crf)}.yuv'

        print(f'Start {codec} Decode for ' + video_name + ' at crf' + str(crf))

        if codec == 'x265' or codec == 'x264' or codec == 'VP9':
            cmd_decode = f'ffmpeg -i {encoded_video} -y {decode_video}'

        print(cmd_decode)
        subprocess.run(cmd_decode, encoding="utf-8", shell=True)
        # os.remove(encoded_video)

    # --------------------VMAF computaion------------------------
    for crf in qp_level:
        decode_video = f'{decode_path}{codec}/{video}_decoded_crf_{str(crf)}.yuv'
        vmaf_name = f'{vmaf_path}{codec}/{video}_decoded_crf_{str(crf)}.csv'

        print('Start VMAF computation for ' + video_name + ' at crf' + str(crf))

        cmd_vmaf = f'ffmpeg -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {decode_video}' \
                   f' -video_size {video_width}x{video_height} -r {framerate} -pix_fmt {pixfmt} -i {orignial_video}' \
                   f' -lavfi "[0:v]setpts=PTS-STARTPTS[reference]; [1:v]setpts=PTS-STARTPTS[distorted]; [distorted][reference]' \
                   f'libvmaf=log_fmt=xml:log_path={vmaf_name}:model_path=../model/vmaf_v0.6.1.json:n_threads=4" ' \
                   f'-f null -'

        print(cmd_vmaf)
        subprocess.run(cmd_vmaf, encoding="utf-8", shell=True)
        os.remove(decode_video)
    os.remove(orignial_video)



