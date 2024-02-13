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
    df_codecs = pd.read_csv(f'../metrics/energy/YOUTUBE_UGC_1080P_{codec}_metrics_energy.csv')

    cat_uniques = df_codecs['category'].unique()
    for cat in cat_uniques:
        cat_data = df_codecs[df_codecs['category'].isin([cat])]
        # print(cat_data)

        avg_bitrate = []
        avg_psnr = []
        avg_vmaf = []
        avg_encode_energy = []
        avg_decode_energy = []
        avg_total_energy = []
        qp_list = []
        std_bitrate = []
        std_psnr = []
        std_vmaf = []
        std_encode_energy = []
        std_decode_energy = []
        std_total_energy = []

        qp_uniques = df_codecs['QP'].unique()
        for qp in qp_uniques:
            qp_data = cat_data[cat_data['QP'].isin([qp])]
            # print(qp_data)

            avg_bitrate.append(qp_data['bitrate_encoded (kb/s)'].mean())
            avg_psnr.append(qp_data['PSNR'].mean())
            avg_vmaf.append(qp_data['VMAF'].mean())
            avg_encode_energy.append(qp_data['target_encode_energy'].mean())
            avg_decode_energy.append(qp_data['decode_energy'].mean())
            avg_total_energy.append(qp_data['energy'].mean())
            qp_list.append(qp)

            std_bitrate.append(qp_data['bitrate_encoded (kb/s)'].std(ddof=0))
            std_psnr.append(qp_data['PSNR'].std(ddof=0))
            std_vmaf.append(qp_data['VMAF'].std(ddof=0))
            std_encode_energy.append(qp_data['target_encode_energy'].std(ddof=0))
            std_decode_energy.append(qp_data['decode_energy'].std(ddof=0))
            std_total_energy.append(qp_data['energy'].std(ddof=0))

        df_avg = pd.DataFrame(columns=['category', 'Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP', 'encode_energy', 'decode_energy', 'total_energy',
                                       'std_bitrate', 'std_psnr', 'std_vmaf', 'std_encode_energy', 'std_decode_energy', 'std_total_energy', 'codec'])
        genre_name = cat
        df_avg['Bitrate (kb/s)'] =avg_bitrate
        df_avg['PSNR (dB)'] = avg_psnr
        df_avg['VMAF'] = avg_vmaf
        df_avg['encode_energy'] = avg_encode_energy
        df_avg['decode_energy'] = avg_decode_energy
        df_avg['total_energy'] = avg_total_energy

        df_avg['std_bitrate'] = std_bitrate
        df_avg['std_psnr'] = std_psnr
        df_avg['std_vmaf'] = std_vmaf
        df_avg['std_encode_energy'] = std_encode_energy
        df_avg['std_decode_energy'] = std_decode_energy
        df_avg['std_total_energy'] = std_total_energy

        df_avg['QP'] = qp_list
        df_avg['codec'] = codec
        df_avg['category'] = genre_name

        print(df_avg)
        # metrics = f'../metrics/YOUTUBE_UGC_1080P_all_average_{genre_name}_{codec}_metrics_energy.csv'
        # df_avg.to_csv(metrics, index=None)
        print('==============================================================================')
        frames.append(df_avg)

df = pd.concat(frames)
# print(df)
metrics_name = f'../metrics/average_QP/YOUTUBE_UGC_1080P_all_average_metrics_energy.csv'
df.to_csv(metrics_name, index=None)

cat_uniques = df['category'].unique()
for cat in cat_uniques:
    cat_data = df[df['category'].isin([cat])]
    print(cat_data)

    genre_name = cat
    # vmaf_encode
    fig_name1 = f'{genre_name}_average_vmaf-encode_energy.png'
    fig_path1 = f'{fig_path}/{fig_name1}'
    print(fig_path1)
    fig1 = sns.lineplot(data=cat_data, x='encode_energy', y='VMAF', hue='codec') #, err_style='bars', errorbar=('ci', 95)
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Encode Energy (kJ)')
    plt.ylabel('VMAF')
    plt.title('VMAF vs Encode Energy')
    plt.savefig(fig_path1, dpi=600)
    plt.show()
    plt.close()

    # psnr_encode
    fig_name2 = f'{genre_name}_average_psnr-encode_energy.png'
    fig_path2 = f'{fig_path}/{fig_name2}'
    print(fig_path2)
    fig2 = sns.lineplot(data=cat_data, x='encode_energy', y='PSNR (dB)', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Encode Energy (kJ)')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR vs Encode Energy')
    plt.savefig(fig_path2, dpi=600)
    plt.show()
    plt.close()

    # vmaf_decode
    fig_name3 = f'{genre_name}_average_vmaf-decode_energy.png'
    fig_path3 = f'{fig_path}/{fig_name3}'
    print(fig_path3)
    fig3 = sns.lineplot(data=cat_data, x='decode_energy', y='VMAF', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Decode Energy (kJ)')
    plt.ylabel('VMAF')
    plt.title('VMAF vs Decode Energy')
    plt.savefig(fig_path3, dpi=600)
    plt.show()
    plt.close()

    # psnr_decode
    fig_name4 = f'{genre_name}_average_psnr-decode_energy.png'
    fig_path4 = f'{fig_path}/{fig_name4}'
    print(fig_path4)
    fig4 = sns.lineplot(data=cat_data, x='decode_energy', y='PSNR (dB)', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Decode Energy (kJ)')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR vs Decode Energy')
    plt.savefig(fig_path4, dpi=600)
    plt.show()
    plt.close()

    # vmaf_total
    fig_name5 = f'{genre_name}_average_vmaf-total_energy.png'
    fig_path5 = f'{fig_path}/{fig_name5}'
    print(fig_path5)
    fig5 = sns.lineplot(data=cat_data, x='total_energy', y='VMAF', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Total Energy (kJ)')
    plt.ylabel('VMAF')
    plt.title('VMAF vs Total Energy')
    plt.savefig(fig_path5, dpi=600)
    plt.show()
    plt.close()

    # psnr_total
    fig_name6 = f'{genre_name}_average_psnr-total_energy.png'
    fig_path6 = f'{fig_path}/{fig_name6}'
    print(fig_path6)
    fig6 = sns.lineplot(data=cat_data, x='total_energy', y='PSNR (dB)', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Total Energy (kJ)')
    plt.ylabel('PSNR')
    plt.title('PSNR vs Total Energy')
    plt.savefig(fig_path6, dpi=600)
    plt.show()
    plt.close()


    # bitrate_encode
    fig_name7 = f'{genre_name}_average_bitrate-encode_energy.png'
    fig_path7 = f'{fig_path}/{fig_name7}'
    print(fig_path7)
    fig7 = sns.lineplot(data=cat_data, x='Bitrate (kb/s)', y='encode_energy', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('Encode Energy (kJ)')
    plt.title('Bitrate vs Encode Energy')
    plt.savefig(fig_path7, dpi=600)
    plt.show()
    plt.close()

    # bitrate_decode
    fig_name8 = f'{genre_name}_average_bitrate-decode_energy.png'
    fig_path8 = f'{fig_path}/{fig_name8}'
    print(fig_path8)
    fig8 = sns.lineplot(data=cat_data, x='Bitrate (kb/s)', y='decode_energy', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('Decode Energy (kJ)')
    plt.title('Bitrate vs Decode Energy')
    plt.savefig(fig_path8, dpi=600)
    plt.show()
    plt.close()

    # bitrate_total
    fig_name9 = f'{genre_name}_average_bitrate-total_energy.png'
    fig_path9 = f'{fig_path}/{fig_name9}'
    print(fig_path9)
    fig9 = sns.lineplot(data=cat_data, x='Bitrate (kb/s)', y='total_energy', hue='codec')
    plt.legend(loc='lower right', fontsize=10, title_fontsize=10)
    plt.xlabel('Bitrate (kb/s)')
    plt.ylabel('Total Energy (kJ)')
    plt.title('Bitrate vs Total Energy')
    plt.savefig(fig_path9, dpi=600)
    plt.show()
    plt.close()