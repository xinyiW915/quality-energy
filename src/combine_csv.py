import os
import pandas as pd
import re

folder_path = '../metrics/energy/x264/'

# 获取文件夹下所有的文件
files = os.listdir(folder_path)

# 用于存储已处理的video_name，防止重复处理
processed_video_names = set()

hardware_data = pd.DataFrame()
for file in files:
    if file.endswith('.csv'):
        video_name = file.rsplit('_', 2)[-2] + '_' + file.rsplit('_', 2)[-1].split('.')[0]
        # print(video_name)

        # 检查是否已处理过这个video_name
        if video_name not in processed_video_names:
            # 添加到已处理集合
            processed_video_names.add(video_name)

            # 找到所有具有相同video_name的文件
            relevant_files = [f for f in sorted(files, reverse=True) if video_name in f]
            print(relevant_files)

            # 创建一个空的DataFrame来存储相同video_name的所有文件数据
            combined_df = pd.DataFrame()

            # 合并相同video_name的所有文件数据
            for relevant_file in relevant_files:
                df = pd.read_csv(os.path.join(folder_path, relevant_file))
                combined_df = pd.concat([combined_df, df], ignore_index=True)

            # 添加video_name列
            combined_df.insert(0, 'video_name', video_name)

            hardware_data = pd.concat([hardware_data, combined_df], ignore_index=True)

hardware_data.to_csv('../metrics/quality_energy_hardware.csv', index=False)