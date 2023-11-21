from fabric import Connection
import pandas as pd
import paramiko
from dateutil.parser import parse
import os

def do_fabric_copy():
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key

    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)

    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    # Copy the power log file...
    conn.run('dir')
    print('-----------get file')
    conn.get('/home/xinyi/tek_power/power_log.csv')

    power_log = pd.read_csv("power_log.csv", names=['time_stamp', 'power'])
    power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])
    print(power_log.head())

def get_power_data(end_time):
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key

    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)

    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    try:
        # run the script
        end_time = str(end_time)
        result = conn.run(f'python /home/xinyi/tek_power/tek_net.py -c /home/xinyi/tek_power/power_log.csv --end_time="{end_time}"', hide=True)

        if result.ok:
            # get output
            output = result.stdout.strip()
            print(f'return: {output}')
        else:
            print('Command execution failed')

        # Download a file from the remote host to the local host
        print('-----------get power_log file-----------')
        remote_path = '/home/xinyi/tek_power/power_log.csv'
        local_path = '/home/um20242/quality-energy/metrics/energy_log/'
        logfile_name = f'{local_path}power_log.csv'

        conn.get(remote=remote_path, local=local_path)
        power_log = pd.read_csv(logfile_name, names=['time_stamp', 'power'])
        power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])
        print(power_log.head())

    finally:
        conn.close()

    # Check if the file exists
    if os.path.exists(logfile_name):
        os.remove(logfile_name) # remove power log file
    else:
        print(f'The file {logfile_name} does not exist.')

    return power_log

if __name__ == '__main__':
    end_time = "2023-06-07 12:08:31.565"
    get_power_data(end_time)
