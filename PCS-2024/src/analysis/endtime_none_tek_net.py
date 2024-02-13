from fabric import Connection
import subprocess
import multiprocessing
import paramiko
import pandas as pd
import datetime
import os

def coding_process(command):
    print("Coding_process started")
    try:
        subprocess.run(command, encoding="utf-8", shell=True)
    except Exception as e:
        print(f"Error in coding_process: {str(e)}")
    finally:
        print("Coding_process completed")

def power_measurement(stop_event):
    print("Power_measurement started")
    host = '10.70.16.98'
    user = 'xinyi'
    private_key_path = '/home/um20242/.ssh/id_rsa'
    passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key
    # Create a Paramiko key object from the decrypted private key file
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
    # Create a Connection object and pass the private key directly
    conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})

    try:
        # Execute Script for power log
        while not stop_event.is_set():
            result = conn.run(f'python /home/xinyi/tek_power/tek_net.py -c /home/xinyi/tek_power/power_log.csv', hide=True)
            if result.ok:
                output = result.stdout.strip()
                print(f'return: {output}')
            else:
                print('Command execution failed')

    except Exception as e:
        print(f"Error in power_measurement: {str(e)}")

    finally:
        conn.close()

def run_parallel_processes(command):

    manager = multiprocessing.Manager()
    stop_event = manager.Event()
    pool = multiprocessing.Pool(processes=2)

    # Asynchronously execute coding_process and power_measurement
    result1 = pool.apply_async(coding_process, args=(command,))
    result2 = pool.apply_async(power_measurement, args=(stop_event,))

    # Wait for coding_process to finish
    result1.get()

    # Set stop_event to stop power_measurement
    stop_event.set()

    # Terminate the pool to stop all processes immediately
    pool.terminate()
    pool.join()

    # test time
    # now = datetime.datetime.now()
    # print(now)
    # print("Power_measurement stopped")

def stop_remote_process(conn, process_name):
    try:
        # Find process IDs
        kill_process = conn.run(f"pgrep -f {process_name}", hide=True)

        if kill_process.ok:
            # Get the list of process IDs
            process_ids = kill_process.stdout.strip().split("\n")
            # print(process_ids)

            # Terminate processes
            for pid in process_ids:
                conn.run(f"kill {pid}")

            print(f"Process {process_name} script terminated successfully")

            # test time
            # now = datetime.datetime.now()
            # print(now)
            print("Power_measurement stopped")

        else:
            print(f"No process found with name {process_name}")

    except Exception as e:
        print(f"Error occurred while stopping the process: {str(e)}")

    finally:
        # Close the connection
        conn.close()


def powerlog_copy(conn):

    try:
        # run the script
        # Download a file from the remote host to the local host
        print('-----------get power_log file-----------')
        remote_path = '/home/xinyi/tek_power/power_log.csv'
        local_path = '/home/um20242/quality-energy-master/metrics/energy_log/'
        logfile_name = f'{local_path}power_log.csv'

        conn.get(remote=remote_path, local=local_path)
        power_log = pd.read_csv(logfile_name, names=['time_stamp', 'power'])
        power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])

    except:
        print('Connection timed out')
        power_log = pd.read_csv(logfile_name, names=['time_stamp', 'power'])
        print(power_log)
        conn.close()

    finally:
        conn.close()
    return power_log

if __name__ == '__main__':
    qp = 12
    # encode_command = f'ffmpeg -s 1920x1080 -r 25.0 -pix_fmt yuv420p -y -i ../videocodec/input/TelevisionClip_1080P-68c6.yuv -c:v libsvtav1 -crf {str(qp)} ../videocodec/encoded/SVT-AV1/TelevisionClip_1080P-68c6_encoded_fps25.0_crf_{str(qp)}.mp4 1>../videocodec/encoded/SVT-AV1/encoded_test_log_crf_{str(qp)}.txt 2>&1'

    # host = '10.70.16.98'
    # user = 'xinyi'
    # private_key_path = '/home/um20242/.ssh/id_rsa'
    # passphrase = 'wxy0915'  # Replace with the passphrase for your encrypted key
    # # Create a Paramiko key object from the decrypted private key file
    # private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)
    # # Create a Connection object and pass the private key directly
    # conn = Connection(host=host, user=user, connect_kwargs={'pkey': private_key})
    #
    # run_parallel_processes(encode_command)
    # stop_remote_process(conn, 'python')
    # power_log = powerlog_copy(conn)
    # print(power_log)