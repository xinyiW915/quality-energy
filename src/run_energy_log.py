from functools import partial
import dateutil.parser
import pandas as pd
import datetime
from datetime import timedelta
from src.analysis.task_energy import calc_energies_on_dataframe, calc_job_energy_on_job_row, calc_job_energy_on_job_row_single

def test_calc_job_energy(count_decode, encode_power, encode_time, decode_power, decode_time):
    start_encode = encode_time[0]
    end_encode = encode_time[-1]

    start_decode = str(decode_time[0])
    end_decode = str(decode_time[-1])
    start_decode = dateutil.parser.parse(start_decode)
    end_decode = dateutil.parser.parse(end_decode)

    count = count_decode
    df = pd.DataFrame(
        data={
              'target_encode': [{'start_time': start_encode, 'end_time': end_encode}],
              'start_time_decode': [start_decode], 'end_time_decode': [end_decode], 'count_decode': [count]
              },
        dtype=object
    )

    dti_e = pd.to_datetime(encode_time)
    power_encode_list = encode_power
    df_power_e = pd.Series(data=power_encode_list, name='power', index=dti_e)
    # print(df_power_e)
    _calc_job_energy_target_encode = partial(calc_job_energy_on_job_row_single, df_power_e,
                                             lambda x: x['target_encode']['start_time'],
                                             lambda x: x['target_encode']['end_time'])
    df['target_encode_energy'] = df.apply(_calc_job_energy_target_encode, axis=1)

    dti_d = pd.to_datetime(decode_time)
    power_decode_list = decode_power
    df_power_d = pd.Series(data=power_decode_list, name='power', index=dti_d)
    # print(df_power_d)
    _calc_job_energy_decode = partial(calc_job_energy_on_job_row, df_power_d,
                                      lambda x: x[f'start_time_decode'],
                                      lambda x: x[f'end_time_decode'],
                                      lambda x: x[f'count_decode'])
    df['decode_energy'] = df.apply(_calc_job_energy_decode, axis=1)

    # # calc energy as new column
    df['energy'] = df[['target_encode_energy', 'decode_energy']].sum(axis=1)

    return df

def get_nearest_power(data, start_time, end_time):
    # index = data.index.get_loc(timestamp,"nearest") #old version
    index_start = data.index.get_indexer([start_time], method='nearest')[0] #new version
    index_end = data.index.get_indexer([end_time], method='nearest')[0]

    # print('-----------test-------------')
    # print(start_time)
    # print(data.iloc[index_start-1])
    # print(index_start-1)
    # print(data.iloc[index_start])
    # print(index_start)
    # print(data.iloc[index_start+1])
    # print(index_start+1)
    # print('-----------test-------------')

    # index_start = index_start + 1
    # index_end = index_end + 1
    power_log = data.reset_index()
    power_select = power_log.loc[index_start:index_end, ['time_stamp', 'power']]#one到two行，ac列
    time_list = power_select['time_stamp'].tolist()
    power_list = power_select['power'].tolist()

    return power_list, time_list

if __name__ == '__main__':
    # x265:2023-03-17, x264:2023-03-21, VP9:2023-03-18, SVT-AV1:2023-03-22
    # power_log = pd.read_csv("../metrics/energy_log/power_log_2023-03-21.csv")
    codec = 'x264'

    power_log = pd.read_csv("../metrics/energy_log/power_log_2023-04-13.csv", names=['time_stamp', 'power'])
    power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])# Converting data types to date types
    power_log = power_log.set_index('time_stamp')# Set date to index

    df_metrics = pd.read_csv(f'../metrics/energy_log/YOUTUBE_UGC_1080P_{codec}_metrics_timestamp.csv')
    # df_metrics = df_metrics.drop(['target_encode_energy'], axis=1)
    print(df_metrics.T)
    df_metrics = df_metrics.rename(columns={'energy': 'total_energy'})
    df_metrics['start_time_encode'] = pd.to_datetime(df_metrics['start_time_encode'])
    df_metrics['end_time_encode'] = pd.to_datetime(df_metrics['end_time_encode'])
    df_metrics['start_time_decode'] = pd.to_datetime(df_metrics['start_time_decode'])
    df_metrics['end_time_decode'] = pd.to_datetime(df_metrics['end_time_decode'])

    count_decode_list = []
    encode_energy_list = []
    decode_energy_list = []
    energy_list = []

    nearest_s_e = []
    nearest_e_e = []
    nearest_s_d = []
    nearest_e_d = []

    count_decode = 1
    for i in range(len(df_metrics)):
        print(df_metrics['vid'][i])
        s_e = df_metrics['start_time_encode'][i]
        e_e = df_metrics['end_time_encode'][i]
        encode_power, encode_time = get_nearest_power(power_log, s_e, e_e)

        s_d = df_metrics['start_time_decode'][i]
        e_d = df_metrics['end_time_decode'][i]
        decode_power, decode_time = get_nearest_power(power_log, s_d, e_d)

        df_energy = test_calc_job_energy(count_decode, encode_power, encode_time, decode_power, decode_time)
        print(df_energy.T)

        count_decode_list.append(count_decode)
        encode_energy_list.append(df_energy['target_encode_energy'][0])
        decode_energy_list.append(df_energy['decode_energy'][0])
        energy_list.append(df_energy['energy'][0])

        nearest_s_e.append(df_energy['target_encode'][0]['start_time'])
        nearest_e_e.append(df_energy['target_encode'][0]['end_time'])
        nearest_s_d.append(df_energy['start_time_decode'][0])
        nearest_e_d.append(df_energy['end_time_decode'][0])

    df_metrics['count_decode'] = count_decode_list
    df_metrics['target_encode_energy'] = encode_energy_list
    df_metrics['decode_energy'] = decode_energy_list
    df_metrics['total_energy'] = energy_list

    # nearest time
    df_metrics['nearest_start_time_encode'] = nearest_s_e
    df_metrics['nearest_end_time_encode'] = nearest_e_e
    df_metrics['nearest_start_time_decode'] = nearest_s_d
    df_metrics['nearest_end_time_decode'] = nearest_e_d

    print(df_metrics.T)
    metrics_name = f'../metrics/energy/YOUTUBE_UGC_1080P_{codec}_metrics_energy_v2.csv'
    df_metrics.to_csv(metrics_name, index=None)

