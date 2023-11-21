import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import statistics

fig_path = '../fig/'

codec = 'VP9' #['x264', 'x265', 'VP9', 'SVT-AV1']
df = pd.read_csv(f'../metrics/YOUTUBE_UGC_1080P_{codec}_metrics.csv')

cat_uniques = df['category'].unique()
for cat in cat_uniques:
    cat_data = df[df['category'].isin([cat])]
    print(cat_data)

    avg_bitrate = []
    avg_psnr = []
    avg_vmaf = []
    std_bitrate = []
    std_psnr = []
    std_vmaf = []

    qp_uniques = df['QP'].unique()
    for qp in qp_uniques:
        qp_data = cat_data[cat_data['QP'].isin([qp])]
        # print(qp_data)
        # df2 = qp_data[['bitrate_encoded (kb/s)', 'PSNR', 'VMAF', 'QP']].describe()
        # print(df2)

        avg_bitrate.append(qp_data['bitrate_encoded (kb/s)'].mean())
        avg_psnr.append(qp_data['PSNR'].mean())
        avg_vmaf.append(qp_data['VMAF'].mean())

        std_bitrate.append(qp_data['bitrate_encoded (kb/s)'].std(ddof=0))
        std_psnr.append(qp_data['PSNR'].std(ddof=0))
        std_vmaf.append(qp_data['VMAF'].std(ddof=0))

    print(avg_bitrate)
    print(avg_psnr)
    print(avg_vmaf)
    print(std_bitrate)
    print(std_psnr)
    print(std_vmaf)

    genre_name = cat
    # vmaf
    fig_name1 = f'{codec}_{genre_name}_average_vmaf-bitrate.png'
    fig_path1 = f'{fig_path}{codec}/average_QP/{fig_name1}'
    print(fig_path1)
    # fig1 = sns.lineplot(x=avg_bitrate, y=avg_vmaf, color="steelblue")
    plt.errorbar(avg_bitrate, avg_vmaf, xerr=std_bitrate, yerr=std_vmaf, capsize=2, capthick=2, color="steelblue")
    plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('VMAF')
    plt.title('VMAF vs Bitrate')
    plt.savefig(fig_path1, dpi=600)
    plt.close()

    #psnr
    fig_name2 = f'{codec}_{genre_name}_average_psnr-bitrate.png'
    fig_path2 = f'{fig_path}{codec}/average_QP/{fig_name2}'
    print(fig_path2)
    # fig2 = sns.lineplot(x=avg_bitrate, y=avg_psnr, color="seagreen")
    fig2 = plt.errorbar(avg_bitrate, avg_psnr, xerr=std_bitrate, yerr=std_psnr, capsize=2, capthick=2, color="seagreen")
    plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR vs Bitrate')
    plt.savefig(fig_path2, dpi=600)
    plt.close()


# 1F77B4 blue
# FF7F0E orange
# 2CA02C green
# D62728 red