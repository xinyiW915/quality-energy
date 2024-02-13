import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
seq_op = 'all'
fig_op = 'bitrate_encode'
codec = 'SVT-AV1'
fig_path = '../fig/'
metrics = pd.read_csv(f'../metrics/energy/YOUTUBE_UGC_1080P_{codec}_metrics_energy_repeat.csv')
# print(metrics.T)

temp_bitrate = []
temp_psnr = []
temp_vmaf = []
temp_qp = []
temp_encode_energy = []
temp_decode_energy = []
temp_energy = []

if not os.path.exists(f'{fig_path}{codec}/'):
  os.makedirs(f'{fig_path}{codec}/')
if not os.path.exists(f'{fig_path}{codec}/energy/'):
  os.makedirs(f'{fig_path}{codec}/energy/')
if not os.path.exists(f'{fig_path}{codec}/average_QP/'):
  os.makedirs(f'{fig_path}{codec}/average_QP/')

if seq_op == 'all':

    if fig_op == 'vmaf_encode':
        fig_name = f'{codec}_vmaf-encode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="target_encode_energy", y="VMAF", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Encode Energy (kJ)')
        plt.ylabel('VMAF')
        plt.title('VMAF vs Encode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'vmaf_decode':
        fig_name = f'{codec}_vmaf-decode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="decode_energy", y="VMAF", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Decode Energy (kJ)')
        plt.ylabel('VMAF')
        plt.title('VMAF vs Decode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'vmaf_total':
        fig_name = f'{codec}_vmaf-total_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="energy", y="VMAF", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Total Energy (kJ)')
        plt.ylabel('VMAF')
        plt.title('VMAF vs Total Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'psnr_encode':
        fig_name = f'{codec}_psnr-encode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="target_encode_energy", y="PSNR", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Encode Energy (kJ)')
        plt.ylabel('PSNR (dB)')
        plt.title('PSNR vs Encode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'psnr_decode':
        fig_name = f'{codec}_psnr-decode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="decode_energy", y="PSNR", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Decode Energy (kJ)')
        plt.ylabel('PSNR (dB)')
        plt.title('PSNR vs Decode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'psnr_total':
        fig_name = f'{codec}_psnr-total_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="energy", y="PSNR", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Total Energy (kJ)')
        plt.ylabel('PSNR')
        plt.title('PSNR vs Total Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'bitrate_encode':
        fig_name = f'{codec}_bitrate-encode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="bitrate_encoded (kb/s)", y="target_encode_energy", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Bitrate (kb/s)')
        plt.ylabel('Encode Energy (kJ)')
        plt.title('Bitrate vs Encode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'bitrate_decode':
        fig_name = f'{codec}_bitrate-decode_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="bitrate_encoded (kb/s)", y="decode_energy", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Bitrate (kb/s)')
        plt.ylabel('Decode Energy (kJ)')
        plt.title('Bitrate vs Decode Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

    elif fig_op == 'bitrate_total':
        fig_name = f'{codec}_bitrate-total_energy.png'
        fig_path = f'{fig_path}{codec}/energy/{fig_name}'
        print(fig_path)
        fig = sns.lineplot(data=metrics, x="bitrate_encoded (kb/s)", y="energy", hue='vid', palette="Accent", sort=False)
        plt.legend(loc='lower right', title='Video Sequence', fontsize=6, title_fontsize=6)
        plt.xlabel('Bitrate (kb/s)')
        plt.ylabel('Total Energy (kJ)')
        plt.title('Bitrate vs Total Energy')
        line_fig = fig.get_figure()
        line_fig.savefig(fig_path, dpi=400)
        plt.close(line_fig)

elif seq_op == 'per':
    for i in range(len(metrics)):
        if i < len(metrics)-1 and metrics['vid'][i] == metrics['vid'][i+1]:
            temp_bitrate.append(metrics['bitrate_encoded (kb/s)'][i])
            temp_psnr.append(metrics['PSNR'][i])
            temp_vmaf.append(metrics['VMAF'][i])
            temp_qp.append(metrics['QP'][i])
            temp_encode_energy.append(metrics['target_encode_energy'][i])
            temp_decode_energy.append(metrics['decode_energy'][i])
            temp_energy.append(metrics['energy'][i])

        else:
            temp_bitrate.append(metrics['bitrate_encoded (kb/s)'][i])
            temp_psnr.append(metrics['PSNR'][i])
            temp_vmaf.append(metrics['VMAF'][i])
            temp_qp.append(metrics['QP'][i])
            temp_encode_energy.append(metrics['target_encode_energy'][i])
            temp_decode_energy.append(metrics['decode_energy'][i])
            temp_energy.append(metrics['energy'][i])

            df_sort = pd.DataFrame(columns=['Bitrate (kb/s)', 'PSNR (dB)', 'VMAF', 'QP', 'target_encode_energy', 'decode_energy', 'energy'])
            df_sort['Bitrate (kb/s)'] = temp_bitrate
            df_sort['PSNR (dB)'] = temp_psnr
            df_sort['VMAF'] = temp_vmaf
            df_sort['QP'] = temp_qp
            df_sort['target_encode_energy'] = temp_encode_energy
            df_sort['decode_energy'] = temp_decode_energy
            df_sort['energy'] = temp_energy

            # print(df_sort)
            df_sort = df_sort.sort_values(by=['QP'])
            video_name = metrics['vid'][i]
            print(df_sort.T)

            if fig_op == 'vmaf_encode':
                fig_name1 = f'{video_name}_vmaf-encode_energy.png'
                fig_path1 = f'{fig_path}{codec}/energy/per/{fig_name1}'
                print(fig_path1)
                fig1 = sns.lineplot(data=df_sort, x="target_encode_energy", y="VMAF", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Encode Energy (kJ)')
                plt.ylabel('VMAF')
                plt.title('VMAF vs Encode Energy')
                line_fig1 = fig1.get_figure()
                line_fig1.savefig(fig_path1, dpi=400)
                plt.close(line_fig1)

            elif fig_op == 'vmaf_decode':
                fig_name2 = f'{video_name}_vmaf-decode_energy.png'
                fig_path2 = f'{fig_path}{codec}/energy/per/{fig_name2}'
                print(fig_path2)
                fig2 = sns.lineplot(data=df_sort, x="decode_energy", y="VMAF", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Decode Energy (kJ)')
                plt.ylabel('VMAF')
                plt.title('VMAF vs Decode Energy')
                line_fig2 = fig2.get_figure()
                line_fig2.savefig(fig_path2, dpi=400)
                plt.close(line_fig2)

            elif fig_op == 'vmaf_total':
                fig_name3 = f'{video_name}_vmaf-total_energy.png'
                fig_path3 = f'{fig_path}{codec}/energy/per/{fig_name3}'
                print(fig_path3)
                fig3 = sns.lineplot(data=df_sort, x="energy", y="VMAF", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Total Energy (kJ)')
                plt.ylabel('VMAF')
                plt.title('VMAF vs Total Energy')
                line_fig3 = fig3.get_figure()
                line_fig3.savefig(fig_path3, dpi=400)
                plt.close(line_fig3)

            elif fig_op == 'psnr_encode':
                fig_name1 = f'{video_name}_psnr-encode_energy.png'
                fig_path1 = f'{fig_path}{codec}/energy/per/{fig_name1}'
                print(fig_path1)
                fig1 = sns.lineplot(data=df_sort, x="target_encode_energy", y="PSNR (dB)", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Encode Energy (kJ)')
                plt.ylabel('PSNR (dB)')
                plt.title('PSNR vs Encode Energy')
                line_fig1 = fig1.get_figure()
                line_fig1.savefig(fig_path1, dpi=400)
                plt.close(line_fig1)

            elif fig_op == 'psnr_decode':
                fig_name2 = f'{video_name}_psnr-decode_energy.png'
                fig_path2 = f'{fig_path}{codec}/energy/per/{fig_name2}'
                print(fig_path2)
                fig2 = sns.lineplot(data=df_sort, x="decode_energy", y="PSNR (dB)", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Decode Energy (kJ)')
                plt.ylabel('PSNR (dB)')
                plt.title('PSNR vs Decode Energy')
                line_fig2 = fig2.get_figure()
                line_fig2.savefig(fig_path2, dpi=400)
                plt.close(line_fig2)

            elif fig_op == 'psnr_total':
                fig_name3 = f'{video_name}_psnr-total_energy.png'
                fig_path3 = f'{fig_path}{codec}/energy/per/{fig_name3}'
                print(fig_path3)
                fig3 = sns.lineplot(data=df_sort, x="energy", y="PSNR (dB)", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Total Energy (kJ)')
                plt.ylabel('PSNR (dB)')
                plt.title('PSNR vs Total Energy')
                line_fig3 = fig3.get_figure()
                line_fig3.savefig(fig_path3, dpi=400)
                plt.close(line_fig3)

            elif fig_op == 'bitrate_encode':
                fig_name1 = f'{video_name}_bitrate-encode_energy.png'
                fig_path1 = f'{fig_path}{codec}/energy/per/{fig_name1}'
                print(fig_path1)
                fig1 = sns.lineplot(data=df_sort, x="bitrate_encoded (kb/s)", y="target_encode_energy", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Bitrate (kb/s)')
                plt.ylabel('Encode Energy (kJ)')
                plt.title('Bitrate vs Encode Energy')
                line_fig1 = fig1.get_figure()
                line_fig1.savefig(fig_path1, dpi=400)
                plt.close(line_fig1)

            elif fig_op == 'bitrate_decode':
                fig_name2 = f'{video_name}_bitrate-decode_energy.png'
                fig_path2 = f'{fig_path}{codec}/energy/per/{fig_name2}'
                print(fig_path2)
                fig2 = sns.lineplot(data=df_sort, x="bitrate_encoded (kb/s)", y="decode_energy", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Bitrate (kb/s)')
                plt.ylabel('Decode Energy (kJ)')
                plt.title('Bitrate vs Decode Energy')
                line_fig2 = fig2.get_figure()
                line_fig2.savefig(fig_path2, dpi=400)
                plt.close(line_fig2)

            elif fig_op == 'bitrate_total':
                fig_name3 = f'{video_name}_bitrate-total_energy.png'
                fig_path3 = f'{fig_path}{codec}/energy/per/{fig_name3}'
                print(fig_path3)
                fig3 = sns.lineplot(data=df_sort, x="bitrate_encoded (kb/s)", y="energy", color="steelblue", sort=False)
                plt.legend(loc='lower right', labels=[f'{codec}'], fontsize=10, title_fontsize=10)
                plt.xlabel('Bitrate (kb/s)')
                plt.ylabel('Total Energy (kJ)')
                plt.title('Bitrate vs Total Energy')
                line_fig3 = fig3.get_figure()
                line_fig3.savefig(fig_path3, dpi=400)
                plt.close(line_fig3)

            # return zero
            temp_bitrate = []
            temp_psnr = []
            temp_vmaf = []
            temp_qp = []
            temp_encode_energy = []
            temp_decode_energy = []
            temp_energy = []
