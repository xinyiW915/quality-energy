import os
import glob
import subprocess

def get_mkv_files(folder_path):
    mkv_files = glob.glob(os.path.join(folder_path, "*.mkv"))
    file_info = []

    for file in mkv_files:
        file_name = os.path.basename(file)
        file_info.append((file_name, file))

    return file_info

def duplicate_video(input_file, output_file, repeat_count):
    ffmpeg_cmd = f'ffmpeg -stream_loop {repeat_count} -i "{input_file}" -c copy "{output_file}"'
    subprocess.call(ffmpeg_cmd, shell=True)

def downsample_video(input_file, output_file1, output_file2):
    cmd_540 = f'ffmpeg -i {input_file} -vf "scale=960:540" {output_file1}'
    subprocess.call(cmd_540, shell=True)

    cmd_720 = f'ffmpeg -i {input_file} -vf "scale=-1280:720" {output_file2}'
    subprocess.call(cmd_720, shell=True)

if __name__ == '__main__':
    input_folder = "../"
    downsample_folder = "./downsample_ugc/"
    duplicate_folder = "./downsample_ugc/duplicate/"
    output_yuv_folder = "./input/"

    mkv_files = get_mkv_files(input_folder)
    for file_name, file_path in mkv_files:
        print("File Name:", file_name)
        print("File Path:", file_path)
        video_name = f'{file_name}.mkv'.replace('.mkv', '')
        print("Video Name:", video_name)
        print()

        # downsample
        output_540p = f'{downsample_folder}{video_name}_downsample_540p.mkv'
        output_720p = f'{downsample_folder}{video_name}_downsample_720p.mkv'
        downsample_video(file_path, output_540p, output_720p)

        # duplicate
        repeat_count = 5
        duplicate_file_540p = f'{duplicate_folder}{video_name}_downsample_540p_duplicate.mkv'
        duplicate_file_720p = f'{duplicate_folder}{video_name}_downsample_720p_duplicate.mkv'

        duplicate_video(output_540p, duplicate_file_540p, repeat_count)
        duplicate_video(output_720p, duplicate_file_720p, repeat_count)

        # --------------------Convert mkv to yuv------------------------
        duplicate_file_540p_yuv = f'{output_yuv_folder}{video_name}_downsample_540p_duplicate.yuv'
        duplicate_file_720p_yuv = f'{output_yuv_folder}{video_name}_downsample_720p_duplicate.yuv'

        print('Convert mkv to yuv ' + duplicate_file_540p)
        cmd_convert = f' ffmpeg -loglevel error -y -i {duplicate_file_540p} -pix_fmt yuv420p -vsync 0 {duplicate_file_540p_yuv}'
        print(cmd_convert)
        subprocess.run(cmd_convert, encoding="utf-8", shell=True)

        print('Convert mkv to yuv ' + duplicate_file_720p)
        cmd_convert = f' ffmpeg -loglevel error -y -i {duplicate_file_720p} -pix_fmt yuv420p -vsync 0 {duplicate_file_720p_yuv}'
        print(cmd_convert)
        subprocess.run(cmd_convert, encoding="utf-8", shell=True)

