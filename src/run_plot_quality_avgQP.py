import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import statistics

fig_op = 'vmaf'
codec_list = ['x264', 'x265', 'VP9', 'SVT-AV1']
fig_path = '../fig/'

frames = []
for codec in codec_list:
    df_codecs = pd.read_csv(f'../metrics/YOUTUBE_UGC_1080P_{codec}_metrics.csv')

    cat_uniques = df_codecs['category'].unique()
    for cat in cat_uniques:
        cat_data = df_codecs[df_codecs['category'].isin([cat])]
        # print(cat_data)

        avg_bitrate = []
        avg_psnr = []
        avg_vmaf = []
        qp_list = []
        std_bitrate = []
        std_psnr = []
        std_vmaf = []

        qp_uniques = df_codecs['QP'].unique()
        for qp in qp_uniques:
            qp_data = cat_data[cat_data['QP'].isin([qp])]
            # print(qp_data)

            avg_bitrate.append(qp_data['bitrate_encoded (kb/s)'].mean())
            avg_psnr.append(qp_data['PSNR'].mean())
            avg_vmaf.append(qp_data['VMAF'].mean())
            qp_list.append(qp)

            std_bitrate.append(qp_data['bitrate_encoded (kb/s)'].std(ddof=0))
            std_psnr.append(qp_data['PSNR'].std(ddof=0))
            std_vmaf.append(qp_data['VMAF'].std(ddof=0))

        df_avg = pd.DataFrame(columns=['category', 'Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP', 'std_bitrate', 'std_psnr', 'std_vmaf', 'codec'])
        genre_name = cat
        df_avg['Bitrate (kb/s)'] =avg_bitrate
        df_avg['PSNR (dB)'] = avg_psnr
        df_avg['VMAF'] = avg_vmaf

        df_avg['std_bitrate'] = std_bitrate
        df_avg['std_psnr'] = std_psnr
        df_avg['std_vmaf'] = std_vmaf

        df_avg['QP'] = qp_list
        df_avg['codec'] = codec
        df_avg['category'] = genre_name

        print(df_avg)
        metrics = f'../metrics/average_QP/YOUTUBE_UGC_1080P_all_average_{genre_name}_{codec}_metrics.csv'
        df_avg.to_csv(metrics, index=None)
        print('==============================================================================')
        frames.append(df_avg)

df = pd.concat(frames)
# print(df)
metrics_name = f'../metrics/average_QP/YOUTUBE_UGC_1080P_all_average_metrics.csv'
df.to_csv(metrics_name, index=None)

cat_uniques = df['category'].unique()
for cat in cat_uniques:
    cat_data = df[df['category'].isin([cat])]
    print(cat_data)

    genre_name = cat
    # vmaf
    fig_name1 = f'{genre_name}_average_vmaf-bitrate.png'
    fig_path1 = f'{fig_path}/{fig_name1}'
    print(fig_path1)
    fig1 = sns.lineplot(data=cat_data, x='Bitrate (kb/s)', y='VMAF', hue='codec') #, err_style='bars', errorbar=('ci', 95)
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('VMAF')
    plt.title('VMAF vs Bitrate')
    plt.savefig(fig_path1, dpi=600)
    plt.show()
    plt.close()

    # psnr
    fig_name2 = f'{genre_name}_average_psnr-bitrate.png'
    fig_path2 = f'{fig_path}/{fig_name2}'
    print(fig_path2)
    fig2 = sns.lineplot(data=cat_data, x='Bitrate (kb/s)', y='PSNR (dB)', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR vs Bitrate')
    plt.savefig(fig_path2, dpi=600)
    plt.show()
    plt.close()


