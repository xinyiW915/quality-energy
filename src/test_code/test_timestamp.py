import datetime
import subprocess
import logging
import sys
# NOTSET（0）、DEBUG（10）、INFO（20）、WARNING（30）、ERROR（40）、CRITICAL（50）
logger = logging.getLogger(__file__)
logging.basicConfig(filename='./logs/output.log', filemode='a', level='DEBUG',
                    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s',
                    datefmt='%Y-%m-%d, %H:%M:%S')

logger.info('This is a log info')
logger.debug('Debugging')
logger.warning('Warning exists')
logger.info('Finish')

ffmpegBin = "C://Users//um20242//ffmpeg//bin//"  # win

# --------------------Convert mkv to yuv------------------------
cmd_convert = f'{ffmpegBin}ffmpeg.exe -y -i ../ugc-dataset/Animation_1080P-05f8.mkv -pix_fmt yuv420p -vsync 0 ../videocodec/input/Animation_1080P-05f8.yuv'
print(cmd_convert)
logger.debug(f'running ffmpeg with command: {cmd_convert}')
subprocess.run(cmd_convert, encoding="utf-8", shell=True)
print('finish')

# --------------------Start Encode------------------------
cmd_encode = f'{ffmpegBin}ffmpeg.exe -s 1920x1080 -r 25.0 -pix_fmt yuv420p -y -i ../videocodec/input/Animation_1080P-05f8.yuv -c:v libx265 -preset veryfast -crf 12 ../videocodec/encoded/x264/Animation_1080P-05f8_encoded_fps25.0_crf_12.mp4'
print(cmd_encode)
logger.debug(f'running ffmpeg with command: {cmd_encode}')
start_time_encode = datetime.datetime.now()
subprocess.run(cmd_encode, encoding="utf-8", shell=True)
logger.debug(subprocess.run(cmd_encode, encoding="utf-8", shell=True))
end_time_encode = datetime.datetime.now()
print(f'start_time_encode: {start_time_encode}')
print(f'end_time_encode: {end_time_encode}')
print('finish')

# # --------------------ffprobe------------------------
# cmd1 = f'ffprobe ../videocodec/encoded/x264/Animation_1080P-05f8_encoded_fps25.0_crf_12.mp4'
# print(cmd1)
# print('finish')

# # --------------------Start Decode------------------------
# # repeat decoding process
#
# cmd_decode = f'ffmpeg -i ../videocodec/encoded/x264/Animation_1080P-05f8_encoded_fps25.0_crf_12.mp4 -y ../videocodec/decoded/Animation_1080P-05f8_decoded_crf_22.yuv'
# start_time_decode = datetime.datetime.now()
# subprocess.run(cmd_decode, encoding="utf-8", shell=True)
# end_time_decode = datetime.datetime.now()
# print(f'start_time_decode: {start_time_decode}')
# print(f'end_time_decode: {end_time_decode}')
# print('finish')


print(logger)


# if process.returncode != 0:
#     logger.error(f'error {process.stdout}')