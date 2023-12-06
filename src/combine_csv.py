import os
import pandas as pd

codec = f'x264'
folder_path = f'../metrics/energy/{codec}/'

# Get all files in the folder
files = os.listdir(folder_path)

# Used to store processed video names to prevent duplicate processing
processed_video_names = set()

hardware_data = pd.DataFrame()
for file in files:
    if file.endswith('.csv'):
        video_name = file.rsplit('_', 2)[-2] + '_' + file.rsplit('_', 2)[-1].split('.')[0]
        # print(video_name)

        # Check if this video name has been processed before.
        if video_name not in processed_video_names:
            # Add to the processed set
            processed_video_names.add(video_name)

            # Find all files with the same video name
            relevant_files = [f for f in sorted(files, reverse=True) if video_name in f]
            print(relevant_files)

            # Create an empty DataFrame to store data from all files with the same video name
            combined_df = pd.DataFrame()

            # Merge data from all files with the same video name
            for relevant_file in relevant_files:
                df = pd.read_csv(os.path.join(folder_path, relevant_file))
                combined_df = pd.concat([combined_df, df], ignore_index=True)

            # Add the video_name column
            combined_df.insert(0, 'video_name', video_name)

            hardware_data = pd.concat([hardware_data, combined_df], ignore_index=True)

hardware_data.to_csv(f'../metrics/quality_energy_hardware_{codec}.csv', index=False)