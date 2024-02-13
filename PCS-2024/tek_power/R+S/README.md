# Rohde & Schwarz HMC8015 Power Measurements over Ethernet

[Progranner's Manual](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/h/hmc80115/HMC8015_SCPImanual_en_01.pdf)

[Manual](https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/h/hmc80115/HMC8015_UserManual_en_05.pdf)

# Usage

## Connection Setup

- Set static IP to ethernet interface on Raspberry Pi
```
sudo nano /etc/dhcpcd.conf
```
- Then give the correct ethernet adapter a static IP, see below for an example
```
interface eth0
static ip_address=192.168.0.11
```
- Give R&S HMC8015 static IP, navigate to the setup menu by selecting the options below (make sure subnet mask also matches Raspberry Pi)
```
SETUP -> Interface -> Parameter
```
- You now should be able to ping the instrument to test for connection
```
ping 192.168.0.10
```

## Logging

- Run script and specify filename
```
python power.py -c foobar.csv
```
- Send a keyboard interrupt (CTRL+C) to stop logging and close file