# quality-energy

# TODOs
## finished tasks
- [x] avg power script (`run_energy_log_avg.py`)
- [x] t-distribution script (`run_codec_metrics_timestamp_logging_repeat_distribution.py`)
- [x] duplicate video and power filter script (`run_codec_metrics_timestamp_logging_duplicate_distribution_energy.py`)
- [x] downsample process and energy script (`run_codec_metrics_downsample.py`)

## preprocessing 
- [x] read bitrate for raw video
- [x] convert mkv to yuv

## encoding  
- [x] repeat 10 times
- [x] encode with 9 QP values
- [x] encode with QP level
- [x] read bitrate for encoded video
- [x] read psnr for encoded video


## decoding
- [ ] repeat 10 times

## vmaf
- [x] calculate vmaf

## energy
- [x] measure time, then get power log
- [x] calculate energy for each encode job

# Main Scripts
- `power_log_extract.py` - extract the power log for a specific date
- `run_codec_metrics.py` - main workflow 

- `run_codec_metrics_timestamp_logging.py` - main workflow with logging
- `run_codec_metrics_timestamp_logging_repeat.py` - main workflow with logging (repeat encoding and decoding process for calculate energy)
- `run_codec_metrics_timestamp_logging_repeat_distribution_energy.py` - main workflow with logging (repeat time with t-distribution)
- `run_codec_metrics_timestamp_logging_duplicate_distribution_energy.py` - main workflow with logging (Duplicate the video and repeat the energy process)
- `run_codec_metrics_downsample.py` - main workflow with downsample process
- - `run_codec_metrics_downsample_4k.py` - main workflow with downsample process for 4k video

- `run_energy_log.py` - calculate energy for each codec: no repeat
- `run_energy_log_repeat.py` - calculate energy for each codec: with repeat encoding and decoding process


- `run_plot_energy_avgQP.py` - plot vmaf/psnr vs. energy: for each genre, get average vmaf/psnr based on different QP levels, plot all te codecs in one figure ('/fig/' folder)
- `run_plot_energy_perSeq_perCod.py` - plot vmaf/psnr vs. energy: for each codec, get vmaf/psnr/bitrate vs. energy, plot all the video sequences in one figure or plot for each video sequence ('/fig/codec/energy/' and '/fig/codec/energy/per/' folder)


- `run_plot_quality_avgQP.py` - plot vmaf/psnr vs. bitrate: for each genre, get average vmaf/psnr based on different QP levels, plot all the codecs in one figure ('/fig/' folder)
- `run_plot_quality_avgQP_perCod.py` - plot vmaf/psnr vs. bitrate: for each codec, average vmaf/psnr based on different QP levels, plot for each video sequence ('/fig/codec/average_QP/' folder)
- `run_plot_quality_perSeq_perCod.py` - plot vmaf/psnr vs. bitrate: for each codec, plot all the video sequences in one figure or plot for each video sequence ('/fig/codec/' folder)


- `run_plot_energy_perCod.ipynb` - energy analysis
- `run_plot_power.ipynb` - plot power vs. timestamp for each video sequence at different QP level ('/fig/power_time_plots/' folder)

# Deployment
- download some original videos from YouTube
1. Find files with `gsutil ls gs://ugc-dataset/original_videos/`
2. Download desired files: e.g. `gsutil -m cp -r 
   gs://ugc-dataset/original_videos/TelevisionClip/1080P/TelevisionClip_1080P
   -68c6.mkv .` -- **make sure to recreate folder structure /<resolution>**
3. keep 'src/logs' folder


[//]: # (cmd)

[//]: # (`ffmpeg -y -i /media/data/video_resized/HowTo/1080P/HowTo_1080P-36a9.mp4 -i /media/data/video_temp/videos/HowTo_1080P-36a9_libx264_22_.mp4 -lavfi libvmaf="model_path=vmaf_v0.6.1.json:log_fmt=json:log_path=output.json" -f null -`)


# 4k test sequences:
Gaming_2160P-2dc4.mkv: 13.9 GB
HDR_2160P-06ae.mkv: 11.1 GB
Sports_2160P-0455.mkv:  7 GB
Vlog_2160P-030a.mkv: 5.6 GB









