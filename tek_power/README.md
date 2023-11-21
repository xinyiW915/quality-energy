# Tektronix PA1000 Power Measurements over Ethernet

[Manual](https://download.tek.com/manual/PA1000_User_Manual_26.pdf)
See p. 54 for commands 

## Example commands
### clear selection
:SEL:CLR

### select measurements
:SEL:VLT
:SEL:AMP
:SEL:FRQ
:SEL:WAT
:SEL:VAS
:SEL:VAR
:SEL:PWF
:SEL:VPK+
:SEL:APK+

### read data
:FRD?
:FRF?

### set 'data available flag'
:DSE 2

### is data available?
:DSR?

### Then read
:FRD?

# Set static IP on RPi
- edit 

```bash
interface eth0
static ip_address=192.168.0.10/24
```

# Run

```bash
TIMESTAMP=`date +%Y-%m-%d_%H-%M-%S`
python tek_net.py >> power_$TIMESTAMP.csv
```


# Alternatives
## USB
Jed Preist has written a [script](https://github.com/sust-cs-uob/measurements/blob/main/Jed/reader.py)
that reads from USB, using the [pyVisa library](https://pyvisa.readthedocs.io/en/latest/). 

However, This requires a 
VISA backend, which is not available for RPi.
https://edadocs.software.keysight.com/kkbopen/linux-io-libraries-faq-589309025.html

