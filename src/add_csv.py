import os
import pandas as pd

codec = f'x264'
folder_path = f'../metrics/rapl_energy/{codec}/'


# add video_name and QP informaiton
csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]

def process_vid(filename):
    video_name = filename.rsplit('_', 2)[-2] + '_' + filename.rsplit('_', 2)[-1].split('.')[0]
    print(video_name)
    if '_downsample_' in filename:
        print(f'{video_name}_downsample_1080p')
        return [f'{video_name}_downsample_1080p', f'{video_name}_downsample_1080p',
                f'{video_name}_downsample_1080p', f'{video_name}_downsample_1080p', f'{video_name}_downsample_1080p',
                f'{video_name}_downsample_720p', f'{video_name}_downsample_720p', f'{video_name}_downsample_720p',
                f'{video_name}_downsample_720p', f'{video_name}_downsample_720p']
    elif '_nodownsample_' in filename:
        return [f'{video_name}'] * 5

def process_qp(filename):
    print(filename)
    if '_downsample_' in filename:
        return [10, 20, 30, 40, 50, 10, 20, 30, 40, 50]
    elif '_nodownsample_' in filename:
        return [10, 20, 30, 40, 50]

for csv_file in csv_files:
    file_path = os.path.join(folder_path, csv_file)

    df = pd.read_csv(file_path)

    df['vid'] = process_vid(csv_file)
    df['QP'] = process_qp(csv_file)
    # print(df.T)
    df.to_csv(file_path, index=False)


# add quality and metadata informaiton
selected_columns = ['category', 'resolution', 'width', 'height', 'pixfmt', 'framerate',
                     'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF']

hardware_data = pd.read_csv(f'../metrics/quality_energy_hardware_{codec}.csv')
software_data = pd.read_csv(f'../metrics/quality_energy_software_rapl_{codec}.csv')

software_data.set_index(['vid', 'QP'], inplace=True)
hardware_data.set_index(['vid', 'QP'], inplace=True)
print(hardware_data)

print(software_data)

selected_columns = ['category', 'resolution', 'width', 'height', 'pixfmt', 'framerate',
                     'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF']

software_data.update(hardware_data[selected_columns])
software_data.reset_index(inplace=True)
print(software_data.columns)
column_order = ['video_name', 'vid', 'category', 'resolution', 'width', 'height', 'pixfmt', 'framerate',
                 'bitrate_rawvideo (kb/s)', 'bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP',
                 'encoding_elapsed_time', 'decoding_elapsed_time',
                 'duplicate_count', 'duplicate_bitrate_rawvideo (kb/s)',
                 'start_time_encode', 'end_time_encode', 'count_encode',
                 'start_time_decode', 'end_time_decode', 'count_decode',
                 'target_encode_energy', 'decode_energy', 'total_energy']

software_data = software_data[column_order]

print(software_data)
software_data.to_csv((f'../metrics/quality_energy_software_rapl_{codec}.csv'), index=False)