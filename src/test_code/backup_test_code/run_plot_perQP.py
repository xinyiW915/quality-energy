import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

metrics = pd.read_csv("../metadata/YOUTUBE_UGC_1080P_metrics.csv")
metrics.sort_values(by=['bitrate_hevc (kb/s)'])

df_sort = pd.DataFrame(columns=['Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP'])
df_sort['Bitrate (kb/s)'] = metrics.sort_values(by=['bitrate_hevc (kb/s)'])['bitrate_hevc (kb/s)'].values.tolist()
df_sort['PSNR (dB)'] = metrics.sort_values(by=['bitrate_hevc (kb/s)'])['PSNR'].values.tolist()
df_sort['VMAF'] = metrics.sort_values(by=['bitrate_hevc (kb/s)'])['VMAF'].values.tolist()
df_sort['QP'] = metrics.sort_values(by=['bitrate_hevc (kb/s)'])['QP'].values.tolist()
print(df_sort)

fig_name1 = 'vmaf-bitrate_QP.png'
fig_name2 = 'psnr-bitrate_QP.png'
# fig_name1 = 'vmaf-bitrate.png'
# fig_name2 = 'psnr-bitrate.png'
fig_path1 = f'../fig/{fig_name1}'
fig_path2 = f'../fig/{fig_name2}'

fig1 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="VMAF", hue='QP', palette="Accent")
plt.legend(loc='lower right', title='QP')
# fig1 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="VMAF", color="steelblue")
# plt.legend(labels=['x265'], loc='upper right')
plt.xlabel('Bitrate (kb/s)')
plt.ylabel('VMAF')
plt.title('VMAF vs Bitrate')
line_fig1 = fig1.get_figure()
line_fig1.savefig(fig_path1, dpi=400)

# # fig2 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="PSNR (dB)", hue='QP', palette="Accent")
# # plt.legend(loc='lower right', title='QP')
# fig2 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="PSNR (dB)", color="steelblue")
# plt.legend(labels=['x265'], loc='upper right')
# plt.xlabel('Bitrate (kb/s)')
# plt.ylabel('PSNR (dB)')
# plt.title('PSNR vs Bitrate')
# line_fig2 = fig2.get_figure()
# line_fig2.savefig(fig_path2, dpi=400)


