import socket
import argparse
import sys
import time
from datetime import datetime
import pandas as pd
import csv

HOST = '192.168.0.10'
PORT = 5025
RECV_BUFFSIZE = 4096
CONFLICT_CODE = 409
LOG_INTERVAL = 1  # seconds


class Rs_power:
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))

    def close(self):
        self.s.close()

    def send(self, msg):
        self.s.send(f"{msg}\n".encode())

    def recv(self):
        data = bytearray()

        while True:
            # may need a time.sleep here as if inst is writing slower than we are reading will break
            packet = self.s.recv(RECV_BUFFSIZE)
            if not packet:
                break
            data.extend(packet)

            if packet[-1:] == b'\n':
                break

        self.data = data.decode()

    # Logs using inbuilt function and stores in internal memory
    # Internal memory is 512KBytes and so only lasts ~1.5hours
    def start_logging(self, filename):
        self.send(f'LOG:FNAM "{filename}"')
        fname = self.query("LOG:FNAM?").strip()

        self.send("LOG ON")
        self.start_time = time.perf_counter()

        log_val = self.query("LOG?").strip()

        if int(log_val) == 0:
            print("Failed to start logging")
            return CONFLICT_CODE
        else:
            print(f"Started logging (Log value: {log_val}, file: {fname})")
            return fname

    # Logs locally by manually reading data, and so only limited by space on logging machine (Pi)
    def start_manual_logging(self, filename):
        # Prepare inst to measure all funcs
        self.send("CHAN:MEAS:FUNC URMS,IRMS,P,FPLL,URange,IRange,S,Q,LAMBDA,UTHD")
        # Have inst identify itself
        idn = self.query("*IDN?").strip().split(',')

        with open(filename, 'a') as f:
            wrtr = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONE)
            # Write header info
            wrtr.writerow(["#Device", idn[1]])
            wrtr.writerow(["#Date", datetime.now().date()])
            wrtr.writerow(["#Version", idn[3]])
            wrtr.writerow(["#Serial No.", idn[2]])
            wrtr.writerow(["#Start Time", datetime.now().time()])
            wrtr.writerow(["#End Time", datetime.now().time()])
            wrtr.writerow("URMS[V],IRMS[A],P[W],FPLL[Hz],URange[V],IRange[A],S[VA],Q[var],LAMBDA[],UTHD[%],Timestamp".split(','))

            try:
                curr_time = None
                while True:
                    res = self.query("CHAN1:MEAS:DATA1?")
                    curr_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    row = f"{res.strip()},{curr_time}"

                    print(row)
                    wrtr.writerow(row.split(','))

                    time.sleep(LOG_INTERVAL)
            except KeyboardInterrupt:
                print("\nKeyboard interrupt, stopping logging")
                f.close()
            finally:
                # To edit end time, need to read and then rewrite data
                logs = []
                with open(filename, 'r') as f:
                    data = csv.reader(f)
                    logs.extend(data)

                end_time = {5: ["#End Time", curr_time]}

                with open(filename, 'w') as f:
                    wrtr = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONE)
                    for line, row in enumerate(logs):
                        data = end_time.get(line, row)
                        wrtr.writerow(data)

                f.close()

    def stop_logging(self):
        self.send("LOG OFF")

        print(f"Stopped logging")

    def query(self, msg):
        self.s.send(f"{msg}\n".encode())
        self.recv()

        return self.data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', '-c', help="to write to")

    args = parser.parse_args(sys.argv[1:])
    # print(args.csv)

    inst = Rs_power(HOST, PORT)
    inst.start_manual_logging(args.csv.upper())
