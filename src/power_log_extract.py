import dateutil.parser
import pandas as pd

if __name__ == '__main__':
    power_log = pd.read_csv("../metrics/energy_log/power_log_2023-03-03.csv", names=['time_stamp', 'power'])
    print(power_log)
    power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])

    df_sort = pd.DataFrame(columns=['time_stamp', 'power'])
    time_stamp_list = []
    power_list = []

    date = '2023-03-22'
    for i in range(len(power_log)):

        power_date = power_log['time_stamp'][i].strftime('%Y-%m-%d')
        if date == power_date:
            time_stamp_list.append(power_log['time_stamp'][i])
            power_list.append(power_log['power'][i])

    df_sort['time_stamp'] = time_stamp_list
    df_sort['power'] = power_list

    df_sort_name = f'../metrics/energy_log/power_log_{date}.csv'
    df_sort.to_csv(df_sort_name, index=None)

    # print(power_log.head(2))
    #
    # power_log.columns = ['time_stamp', 'power']
    # power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])  # 将数据类型转换为日期类型
    # power_log = power_log.set_index('time_stamp')  # 将date设置为index
    # print(power_log.head(2))
    # print(power_log.tail(2))
    # print(power_log.shape)
    #
    # print(type(power_log))
    # print(power_log.index)
    # print(type(power_log.index))


