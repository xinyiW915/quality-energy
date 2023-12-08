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
    ffmpeg_cmd = f'{ffmpegBin}ffmpeg.exe -stream_loop {repeat_count} -i "{input_file}" -c copy "{output_file}"'
    subprocess.call(ffmpeg_cmd, shell=True)

if __name__ == '__main__':
    ffmpegBin = "C://Users//um20242//ffmpeg//bin//" #win

    # input_folder = "/home/um20242/quality-energy/ugc-dataset"
    input_folder = "../"
    output_folder = "./"

    mkv_files = get_mkv_files(input_folder)
    for file_name, file_path in mkv_files:
        print("File Name:", file_name)
        print("File Path:", file_path)
        print()

        repeat_count = 5
        output_file = output_folder + file_name
        duplicate_video(file_path, output_file, repeat_count)

        # --------------------Convert mkv to yuv------------------------
        video_name = f'{file_name}.mkv'.replace('.mkv', '')
        orignial_video = f'{output_folder}{video_name}.yuv'
        print('Convert mkv to yuv ' + output_file)
        cmd_convert = f'{ffmpegBin}ffmpeg.exe -loglevel error -y -i {output_file} -pix_fmt yuv420p -vsync 0 {orignial_video}'
        print(cmd_convert)
        subprocess.run(cmd_convert, encoding="utf-8", shell=True)

        os.remove(output_file)
