import traceback
from functools import partial

import dateutil.parser
import pandas as pd
import logging

logger = logging.getLogger(__file__)
logging.basicConfig(filename="logs/analysis.log", filemode='a', level='DEBUG',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y/%m/%d %M%H:%M:%S')

def calc_job_energy_on_job_row(df_power, fn_get_start_time_from_dict_like, fn_get_end_time_from_dict_like,
                               fn_get_job_count_from_dict_like, job, fn_get_array_container=None,
                               fn_calc_energy_in_interval=None):
    """
    Given a pandas row iterator (dict like)
    provide item access functions to get start and end time.

        e.g. calc_job_energy( df_power, lambda x: x['start_time'], lambda x: x['end_time'])


    Optionally, provide an item access function that gets an array container to iterate over.

    for records such {eval_qps: [{'qp': '27',         'start_time': '2021-11-27 02:07:02',         'end_time': '2021-11-27 02:08:09',
     {'qp': '33',   'start_time': '2021-11-27 02:08:09',   'end_time': '2021-11-27 02:09:14',
     ...
    ]}

    e.g. calc_job_energy( df_power, lambda x: x['start_time'], lambda x: x['end_time'], lambda x: x['evaluated_qps'])


    :param fn_calc_energy_in_interval: the function to use, taking (df_power, start_time, end_time) parameters. if None - ::calc_energy_in_interval is used
    :param df_power - data frame with power measurements
    :param fn_get_start_time_from_dict_like:
    :param fn_get_end_time_from_dict_like:
    :param fn_get_job_count_from_dict_like:
    :param job:
    :param fn_get_array_container:
    :return:
    """
    try:

        if fn_get_array_container is None:
            fn_get_array_container = lambda x: [job]

        _array = fn_get_array_container(job)
        energies = []
        for i in _array:
            start_time = fn_get_start_time_from_dict_like(i)
            end_time = fn_get_end_time_from_dict_like(i)
            job_count = fn_get_job_count_from_dict_like(i)
            # print(start_time,end_time,job_count)
            fn_calc_energy = calc_energy_in_interval
            if fn_calc_energy_in_interval is not None:
                fn_calc_energy = fn_calc_energy_in_interval
            item_energy = fn_calc_energy(df_power, start_time, end_time, row=job) / job_count
            energies.append(item_energy)
    except Exception as e:
        tb = traceback.format_exc()
        # print(tb)
        # logger.debug(job['evaluated_qps'])
        logger.debug(job)
        logger.error(e)
        logger.error(str(tb))

        raise e

    return sum(energies)

def calc_job_energy_on_job_row_single(df, fn_start_time, fn_end_time, job, fn_get_array_container=None):
    return calc_job_energy_on_job_row(df, fn_start_time, fn_end_time, lambda x: 1, job,
                                      fn_get_array_container=fn_get_array_container)


def calc_energy_in_interval(df, start_time, end_time, row=None):
    # "2021-11-25 15:02:16"

    interval_start = dateutil.parser.parse(str(start_time))
    interval_end = dateutil.parser.parse(str(end_time))

    start = df.index.searchsorted(interval_start)
    end = df.index.searchsorted(interval_end)

    interval = df.iloc[start: end]

    duration = (interval_end - interval_start).total_seconds()

    energy = interval.mean() * duration

    return energy

def calc_energies_on_dataframe(df_done: pd.DataFrame, df_power: pd.DataFrame = None, _calc_job_energy_decode=None, flag_calc_resize=True):
    def fn_resize_calc_energy_in_interval_original(df_power, start_time, end_time, row):
        assert 'original' in row
        if row['original']:
            # no resizing for original videos
            return 0

        return calc_energy_in_interval(df_power, start_time, end_time)

    _calc_job_energy_resize = partial(calc_job_energy_on_job_row, df_power, lambda x: x.resize_start_datetime,
                                      lambda x: x.resize_end_datetime, lambda x: x.resize_count,
                                      fn_calc_energy_in_interval=fn_resize_calc_energy_in_interval_original)
    # calc energy as new column

    _calc_job_energy_target_encode = partial(calc_job_energy_on_job_row_single, df_power,
                                             lambda x: x['target_encode']['start_time'],
                                             lambda x: x['target_encode']['end_time'])

    _calc_job_energy_qp_finding_encode = partial(calc_job_energy_on_job_row_single, df_power,
                                                 lambda x: x['start_time'],
                                                 lambda x: x['end_time'],
                                                 fn_get_array_container=lambda x: x['evaluated_qps'])
    if _calc_job_energy_decode is None:
        _calc_job_energy_decode = partial(calc_job_energy_on_job_row, df_power, lambda x: x.decoding['start_time'],
                                          lambda x: x.decoding['end_time'], lambda x: x.decoding['count'])

    # # calc energy as new column
    df_done['decode_energy'] = df_done.apply(_calc_job_energy_decode, axis=1)
    df_done['evaluated_qps_energy'] = df_done.apply(_calc_job_energy_qp_finding_encode, axis=1)
    if flag_calc_resize:
        df_done['resize_energy'] = df_done.apply(_calc_job_energy_resize, axis=1)
        df_done['preprocessing_energy'] = df_done.resize_energy + df_done.evaluated_qps_energy
    else:
        df_done['preprocessing_energy'] = df_done.evaluated_qps_energy

    df_done['target_encode_energy'] = df_done.apply(_calc_job_energy_target_encode, axis=1)
    #
    df_done['encoding_energy'] = df_done[['target_encode_energy', 'preprocessing_energy']].sum(axis=1)
    #
    df_done['energy'] = df_done[['target_encode_energy', 'preprocessing_energy', 'decode_energy']].sum(axis=1)