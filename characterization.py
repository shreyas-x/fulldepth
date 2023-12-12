from fulldepth import FullDepth
from os import _exit
import serial, time, telnetlib, csv
from datetime import datetime as dt
from statistics import pstdev, mean, median
from pbbx import ProgressBar

REV_TIME = 2.5
WAI_TIME = 0.8
RUN_TIME = 3
ACQ_TIME = 2.5      # acquisition is at the trailing end of runtime
STP_TIME = 3 * 60

# RPMS = [600, 900, 1200, 1500, 1800, 2100, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3690, 3740]
RPMS = [2400, 2600, 2800, 3000, 3200, 3400, 3600, 3690, 3740]

VOLTAGE = 305

DIR = 'f'
DIR_SIGN = 1 if DIR == 'f' else -1

THRUSTER = "T150"
# T150_MOMENT = 0.4356
# T180_MOMENT = 0.4122
MOMENT = 0.4356 if THRUSTER == "T150" else 0.4122

# Setup thruster
t = FullDepth(com='COM9', addr=b'\x00')

def send_read_ps_telnet(tel):
    tel.write(b"MEAS:CURR?\n")
    time.sleep(0.1)
    (_, m, _) = tel.expect([b"[-+]?\d*\.?\d+"], timeout=0.1)
    try:
        c = float(m[0].decode('ascii').strip())
        if c > 0 and c < 10:
            return c 
    except ValueError:
        pass
    except TypeError:
        pass

    return 0.0

def calc_median(arr):
    std = pstdev(arr)
    avg = mean(arr)

    # eliminate measurements that are more than 2 standard deviations away from the mean
    arr = [f if (f < avg+(2*std) or f > avg-(2*std)) else 0 for f in arr]
    med = median(arr)
    return med

def run(t):
    
    # Setup telnet client to talk to power supply
    tn = telnetlib.Telnet("192.168.200.100", port=23)
    tn.read_very_eager()
    # Setup load cell
    ms = serial.Serial("COM13", 9600)
    ms.set_buffer_size(rx_size=0)

    test_time = dt.now()
    time_str = test_time.strftime("%d-%m-%y-%H-%M-%S")

    # Prepare output files
    print(f"Started at {test_time.strftime('%H:%M:%S')}")
    main_filename = f"tests/test-{time_str}-main-{'forward' if DIR=='f' else 'reverse'}.csv"
    main_file = open(main_filename, "w", newline="")
    main_writer = csv.writer(main_file)
    main_writer.writerow(["Voltage", "Motor Current", "Input Current", "Set RPM", "Read RPM"])
    thrust_filename = f"tests/test-{time_str}-thrusts-{'forward' if DIR=='f' else 'reverse'}.csv"
    thrust_file = open(thrust_filename, "w", newline="")
    thrust_writer = csv.writer(thrust_file)
    thrust_writer.writerow(["Force", "Thrust"])

    for rpm in RPMS:
        # zero the load cell
        ms.write(b'Z')
        time.sleep(1)

        init = time.time()

        # Reverse thruster at half rpm
        rev_rpm = -1 * int(rpm/2)
        print(f"\nReversing thruster at {rev_rpm:.0f} RPM")
        t.sendRPM(DIR_SIGN * rev_rpm)
        while (time.time() - init < REV_TIME):
            time.sleep(0.2)

        # Stop thruster
        t.stopThruster()
        time.sleep(WAI_TIME)

        # Run thruster
        print(f"Running at {rpm} RPM for {RUN_TIME} s")
        
        ms.reset_input_buffer()
        init = time.time()
        while (time.time() - init < RUN_TIME):
            t.sendRPM(DIR_SIGN * rpm)
            # reply_rpm = t.askForData("rpm")
            # time.sleep(0.05)
            # reply_cur = t.askForData("d_axis_current")
            # time.sleep(0.05)
            # print(reply_rpm, reply_cur)
            reply_rpm = 0.0
            reply_cur = 0.0
            ps_current = send_read_ps_telnet(tn)

            row = [VOLTAGE, reply_cur, ps_current, rpm, reply_rpm]
            main_writer.writerow(row)

            # time.sleep(0.1)

        if ms.in_waiting > 1235:
            lc_data = ms.read_all()[:1234].split(b"\n")
        else:
            lc_data = ms.read_all().split(b"\n")
        lc_data_f = []
        for x in lc_data:
            try:
                f = float(x[2:-1])
                lc_data_f.append(f)
                thrust_writer.writerow([f, f * MOMENT])
            except ValueError:
                lc_data_f.append(0.0)
        median_thrust = calc_median(lc_data_f[int(len(lc_data)/2):]) * MOMENT
        if DIR == 'f':
            max_thrust = max(lc_data_f) * MOMENT
        else:
            max_thrust = min(lc_data_f) * MOMENT
        print(f"Median thrust for {rpm} RPM is {median_thrust:.2f} kgf, max thrust is {max_thrust:.2f} kgf")

        # Stop thruster
        print("Stopping...", end="")
        t.stopThruster()
        print(" thruster stopped")

        # Wait for water to settle
        if (rpm != RPMS[-1]):
            pb = ProgressBar(STP_TIME, "water to settle")
            init = pb.start()
            while (time.time() - init < STP_TIME):
                time.sleep(1)
                pb.update()
    
    # Cleaning up
    tn.close()
    ms.close()
    main_file.close()
    thrust_file.close()
    print(f"Done! Files {time_str} saved")


if __name__ == "__main__":
    try:
        run(t)
    except KeyboardInterrupt:
        t.stopThruster()
        _exit(130)