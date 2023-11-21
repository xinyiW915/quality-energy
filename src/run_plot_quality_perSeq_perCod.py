import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

seq_op = 'all'
fig_op = 'vmaf'
codec = 'x265'
fig_path = '../fig/'
metrics = pd.read_csv(f'../metrics/YOUTUBE_UGC_1080P_{codec}_metrics.csv')

temp_bitrate = []
temp_psnr = []
temp_vmaf = []
temp_qp = []

if seq_op == 'per':
    for i in range(len(metrics)):
        if i < len(metrics)-1 and metrics['vid'][i] == metrics['vid'][i+1]:
            temp_bitrate.append(metrics['bitrate_encoded (kb/s)'][i])
            temp_psnr.append(metrics['PSNR'][i])
            temp_vmaf.append(metrics['VMAF'][i])
            temp_qp.append(metrics['QP'][i])
        else:
            temp_bitrate.append(metrics['bitrate_encoded (kb/s)'][i])
            temp_psnr.append(metrics['PSNR'][i])
            temp_vmaf.append(metrics['VMAF'][i])
            temp_qp.append(metrics['QP'][i])
            df_sort = pd.DataFrame(columns=['Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP'])
            df_sort['Bitrate (kb/s)'] = temp_bitrate
            df_sort['PSNR (dB)'] = temp_psnr
            df_sort['VMAF'] = temp_vmaf
            df_sort['QP'] = temp_qp
            # print(df_sort)
            df_sort = df_sort.sort_values(by=['Bitrate (kb/s)'])
            print(df_sort)
            video_name = metrics['vid'][i]

            if fig_op == 'vmaf':
                fig_name1 = f'{video_name}_vmaf-bitrate.png'
                fig_path1 = f'{fig_path}{codec}/{fig_name1}'
                print(fig_path1)
                fig1 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="VMAF", color="steelblue")
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Bitrate (kb/s)')
                plt.ylabel('VMAF')
                plt.title('VMAF vs Bitrate')
                line_fig1 = fig1.get_figure()
                line_fig1.savefig(fig_path1, dpi=400)
                plt.close(line_fig1)
            elif fig_op == 'psnr':
                fig_name2 = f'{video_name}_psnr-bitrate.png'
                fig_path2 = f'{fig_path}{codec}/{fig_name2}'
                print(fig_path2)
                fig2 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="PSNR (dB)", color="steelblue")
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Bitrate (kb/s)')
                plt.ylabel('PSNR (dB)')
                plt.title('PSNR vs Bitrate')
                line_fig2 = fig2.get_figure()
                line_fig2.savefig(fig_path2, dpi=400)
                plt.close(line_fig2)

            # return zero
            temp_bitrate = []
            temp_psnr = []
            temp_vmaf = []
            temp_qp = []

elif seq_op == 'all':
    metrics.sort_values(by=['bitrate_encoded (kb/s)'])
    # print(metrics)

    df_sort = pd.DataFrame(columns=['vid', 'Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP'])
    df_sort['vid'] = metrics.sort_values(by=['bitrate_encoded (kb/s)'])['vid'].values.tolist()
    df_sort['Bitrate (kb/s)'] = metrics.sort_values(by=['bitrate_encoded (kb/s)'])['bitrate_encoded (kb/s)'].values.tolist()
    df_sort['PSNR (dB)'] = metrics.sort_values(by=['bitrate_encoded (kb/s)'])['PSNR'].values.tolist()
    df_sort['VMAF'] = metrics.sort_values(by=['bitrate_encoded (kb/s)'])['VMAF'].values.tolist()
    df_sort['QP'] = metrics.sort_values(by=['bitrate_encoded (kb/s)'])['QP'].values.tolist()
    print(df_sort)

    if fig_op == 'vmaf':
        fig_name1 = f'{codec}_vmaf-bitrate.png'
        fig_path1 = f'{fig_path}{codec}/{fig_name1}'
        print(fig_path1)
        fig1 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="VMAF", hue='vid', palette="Accent")
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Bitrate (kb/s)')
        plt.ylabel('VMAF')
        plt.title('VMAF vs Bitrate')
        line_fig1 = fig1.get_figure()
        line_fig1.savefig(fig_path1, dpi=400)
        plt.close(line_fig1)

    elif fig_op == 'psnr':
        fig_name2 = f'{codec}_psnr-bitrate.png'
        fig_path2 = f'{fig_path}{codec}/{fig_name2}'
        print(fig_path2)
        fig2 = sns.lineplot(data=df_sort, x="Bitrate (kb/s)", y="PSNR (dB)", hue='vid', palette="Accent")
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Bitrate (kb/s)')
        plt.ylabel('PSNR (dB)')
        plt.title('PSNR vs Bitrate')
        line_fig2 = fig2.get_figure()
        line_fig2.savefig(fig_path2, dpi=400)
        plt.close(line_fig2)






