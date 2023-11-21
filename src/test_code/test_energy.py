import re

from functools import partial
import dateutil.parser
import pandas as pd
import datetime
from src.analysis.task_energy import calc_job_energy_on_job_row, calc_job_energy_on_job_row_single

def get_info(output, patt, info_name):
    # output_text = re.findall(findtext, output) #"bitrate:+..+kb/s"  "PSNR+......+"
    pattern = re.compile(patt)
    output_text = pattern.findall(output)
    info = "".join(output_text)
    info = info.replace(info_name, "")
    return info

def test_calc_job_energy(s, e):
    # s = '2022-02-14 05:40:00.000'
    # e = '2022-02-14 05:41:00.000'
    s = str(s)
    e = str(e)
    start = dateutil.parser.parse(s)
    end = dateutil.parser.parse(e)

    count = 1
    df = pd.DataFrame(
        data={
              'target_encode': [{'start_time': s, 'end_time': e}],
              'start_time_decode_vlc': [start], 'end_time_decode_vlc': [end], 'count_decode_vlc': [count]
              },
        dtype=object
    )

    dti = pd.to_datetime([s, e, e])
    df_power = pd.Series(data=[100,100,100], name='power', index=dti)


    _calc_job_energy_target_encode = partial(calc_job_energy_on_job_row_single, df_power,
                                             lambda x: x['target_encode']['start_time'],
                                             lambda x: x['target_encode']['end_time'])
    suffix = 'vlc'
    _calc_job_energy_decode = partial(calc_job_energy_on_job_row, df_power,
                                      lambda x: x[f'start_time_decode_{suffix}'],
                                      lambda x: x[f'end_time_decode_{suffix}'],
                                      lambda x: x[f'count_decode_{suffix}'])

    # # calc energy as new column
    df['decode_energy'] = df.apply(_calc_job_energy_decode, axis=1)

    df['target_encode_energy'] = df.apply(_calc_job_energy_target_encode, axis=1)

    df['energy'] = df[['target_encode_energy', 'decode_energy']].sum(axis=1)
    print(df.T)
    # df.to_csv('../energy_logs/test.csv', index=None)


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    print(start_time)
    end_time = datetime.datetime.now()
    print(end_time)
    test_calc_job_energy(start_time, end_time)