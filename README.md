# cissflux

Python 3.x Command Line Utility for saving Sensor Information from [Bosch CISS](https://www.bosch-connectivity.com/products/connected-industrial-sensor-solution/) into InfluxDB via UDP


## Installation and Development

### Installation
Clone the repository to your machine and use `pip` to install the CLI:

    pip install .

### Development
develop using `venv` as follows:

    python -m venv venv

activate the virtual environment, install using:

    pip install -e .


## Usage

In order to access the USB Port, you might need to change ownership (`sudo chown -R user:user /dev/ttyUSB0`) of the serial port or use `sudo`

```
usage: cissflux [-h] --node NODE --serialport SERIALPORT --udp-port UDP_PORT
                [--updaterate UPDATERATE] [--resolution RESOLUTION]
                [--db-host DB_HOST] [--db-port DB_PORT]

CLI for acquiring CISS values and storing it in InfluxDB

optional arguments:
  -h, --help            show this help message and exit
  --node NODE           Node Name for CISS. Used as Tag for InfluxDB
  --serialport SERIALPORT
                        Serial USB Port for CISS
  --udp-port UDP_PORT   UDP Port for sending information via UDP. Should also
                        be configured in InfluxDB
  --updaterate UPDATERATE
                        Update Rate for CISS Module in us. Default: 100ms
  --resolution RESOLUTION
                        Resolution for CISS Accelerometer Module in G.
                        Default: 16G
  --db-host DB_HOST     hostname for InfluxDB HTTP Instance. Default:
                        localhost
  --db-port DB_PORT     port number for InfluxDB HTTP Instance. Default: 8086
```

- You can mention the name of the node, e.g. `CISS1` or similar to use it as a `tag` in InfluxDB
- You can mention the USB Serial Port explicitly e.g. `/dev/ttyUSB0` or `COM3`
- You can mention the UDP Port for the Sensor set in the `influxdb.conf` under the `[[udp]]` section
- You can change the location of the log file in the `cissflux/cissflux.py` file
- You can change the location of the minimal configuration file in `cissflux/cissflux.py` file

### Example

Typical Example:

1. Setup InfluxDB's configuration (`influxdb.conf`) by adding a UDP port to read CISS information:

        [[udp]]
          enabled=true
          bind-address=":8100"
          database=CISS
          precision='u'

2. Run the script using:

        cissflux --serialport COM3 --udp-port 8100 --node testCISS

Data will be stored in `CISS` Database.

3. If run as default the `CONF_PATH` JSON file which contains the minimum configuration file will be executed:

        cissflux # using file conf.json

## Sensors Available

* Current Version provides extraction of only Inertial Sensors:
    - Accelerometer
    - Magnetometer
    - Gyroscope

* Environmental Sensors need to added next [__WIP__]