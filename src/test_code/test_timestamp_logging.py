import datetime
import subprocess
import logging.config
import logging
import sys
import yaml
import shlex

# 读取日志配置文件内容
# logging.basicConfig(filename='./logs/output.log', filemode='a', level='DEBUG',
#                     format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s',
#                     datefmt='%Y-%m-%d, %H:%M:%S')
# 创建一个日志器logger
# logger = logging.getLogger(__file__)
# logger.info('This is a log info')
# logger.debug('Debugging')
# logger.warning('Warning exists')
# 将日志打印在控制台
# logger.debug('打印日志级别：debug')
# logger.info('打印日志级别：info')
# logger.warning('打印日志级别：warning')
# logger.error('打印日志级别：error')
# logger.critical('打印日志级别：critical')

with open('logging.yml', 'r') as file_logging:
    dict_conf = yaml.load(file_logging, Loader=yaml.FullLoader)
logging.config.dictConfig(dict_conf)

logger = logging.getLogger('default')
logger.info('This is a log info')

def measure_command_process(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    print(process)
    return process

def measure_command_runtime(cmd):
    logger.debug(f'running ffmpeg with command: {cmd}')
    start_time = datetime.datetime.now()
    process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, universal_newlines=True)
    print(process)
    end_time = datetime.datetime.now()
    return start_time, end_time, process

# --------------------Convert mkv to yuv------------------------
cmd_convert = f'ffmpeg -y -i ../ugc-dataset/TelevisionClip_1080P-68c6.mkv -pix_fmt yuv420p -vsync 0 ../videocodec/input/TelevisionClip_1080P-68c6.yuv'
print(cmd_convert)
process_convert = measure_command_process(cmd_convert)
if process_convert.returncode != 0:
    logger.error('error: process.returncode != 0')
    raise ValueError(process_convert.stdout)

# --------------------Start Encode------------------------
cmd_encode = f'ffmpeg -s 1920x1080 -r 25.0 -pix_fmt yuv420p -y -i ../videocodec/input/TelevisionClip_1080P-68c6.yuv -c:v libsvtav1 -crf 12 ../videocodec/encoded/out.mp4 1>output.txt 2>&1'
start_time_encode, end_time_encode= measure_command_process(cmd_encode)
print(f'start_time_encode: {start_time_encode}')
print(f'end_time_encode: {end_time_encode}')


# --------------------ffprobe------------------------
cmd1 = f'ffprobe ../videocodec/encoded/x264/Animation_1080P-05f8_encoded_fps25.0_crf_12.mp4'
logger.debug(f'running ffmpeg with command: {cmd1}')

# # --------------------Start Decode------------------------
# # repeat decoding process
#
# cmd_decode = f'ffmpeg -y -i ../videocodec/encoded/x264/Animation_1080P-05f8_encoded_fps25.0_crf_12.mp4 -y ../videocodec/decoded/x264/Animation_1080P-05f8_decoded_crf_22.yuv'
# start_time_decode, end_time_decode, process_decode = measure_command_process(cmd_decode)
# print(f'start_time_decode: {start_time_decode}')
# print(f'end_time_decode: {end_time_decode}')
# if process_decode.returncode != 0:
#     logger.error('error: process.returncode != 0')
#     raise ValueError(process_decode.stdout)

print('finish')
logger.info('Finish')
