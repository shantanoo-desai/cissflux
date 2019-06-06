import sys
import argparse
import logging

from .CISS import ciss
import serial
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

handler = logging.FileHandler("/var/log/cissinflux.log")
handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s-%(name)s-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

com = None
client = None

def write_to_influx(db_client, data_points, node_name):
    """Function to format the data points to UDP packets format for InfluxDB and send them to dedicated DB"""
    _packet = {'points': data_points, 'tags': {'node': node_name}}
    logger.debug('Packet to Send: {}'.format(_packet))
    try:
        db_client.send_packet(_packet)
        logger.info('UDP packet sent')
    except InfluxDBClientError as e:
        logger.exception('Exception during UDP Packet Send for InfluxDB')
        db_client.close()
        raise(e)


def send_data(node_name,serialport, updaterate, resolution, db_host, db_port, udp_port):
    """Function to Setup CISS Node and extract sensor information from it via Serial Port and sending
        the information to InfluxDB via UDP
    """
    logger.info('reading at {} every {}s for Node {}'.format(serialport, resolution/(10**6), node_name))
    try:
        ciss_module = ciss(serialport)
        logger.info('Disable All Sensors Initially for Setup')
        ciss_module.disable_all_sensors()
        logger.info('configuring accelerometer resolution to {}G'.format(resolution))
        ciss_module.set_acc_range(resolution)
        logger.info('configuring update_rate (sampling)')
        ciss_module.set_sampling(updaterate)
        global com
        com = serial.Serial(serialport, baudrate=115200, timeout=None)
        global client
        try:
            logger.info('Creating InfluxDB Connection')
            client = InfluxDBClient(host=db_host, port=db_port, use_udp=True, udp_port=udp_port)
        except InfluxDBClientError as e:
            logger.exception('Exception During InfluxDB Client Creation')
            client.close()
            raise(e)
        logger.info('Reading Sensor Information from Port')
        while True:
            data = bytearray(com.read_until(b'\xfe'))
            data.pop()  # remove the SOF of next frame
            if data:
                # print(data)
                # print('data from port')
                if ciss_module.check_payload(data):
                    # print('after check')
                    # print(data)
                    sensor_data_points = ciss_module.parse_payload(data)
                    logger.debug('Data From Sensor: {}'.format(sensor_data_points))
                logger.info('Writing to InfluxDB')
                write_to_influx(client, sensor_data_points, node_name)
    except Exception as e:
        logger.exception('Exception within `send_data` function')
        com.close()
        client.close()
        raise(e)
        


def parse_args():
    """Pass Arguments"""

    parser = argparse.ArgumentParser(description='CLI for acquiring CISS values and storing it in InfluxDB')

    parser.add_argument('--node', type=str, required=True, help='Node Name for CISS. Used as Tag for InfluxDB')
    
    parser.add_argument('--serialport', type=str, required=True, help='Serial USB Port for CISS')

    parser.add_argument('--udp-port', type=int, required=True, default=8086,
                        help='UDP Port for sending information via UDP.\n Should also be configured in InfluxDB')


    parser.add_argument('--updaterate', type=int, required=False, default=100000, help='Update Rate for CISS Module in us. Default: 100ms')

    parser.add_argument('--resolution', type=int, required=False, default=16, help='Resolution for CISS Accelerometer Module in G. Default: 16G')

    parser.add_argument('--db-host', type=str, required=False, default='localhost',
                        help='hostname for InfluxDB HTTP Instance. Default: localhost')

    parser.add_argument('--db-port', type=int, required=False, default=8086,
                        help='port number for InfluxDB HTTP Instance. Default: 8086')
    
    

    return parser.parse_args()


def main():
    args = parse_args()

    if len(sys.argv) > 1:
        if args.serialport is None:
            print('Provide USB Port for the Sensor')
            sys.exit(1)
        elif args.udp_port is None:
            print('Provide UDP Port for InfluxDB')
        else:
            try:
                send_data(node_name=args.node,
                        serialport= args.serialport,
                        updaterate=args.updaterate,
                        resolution=args.resolution,
                        db_host=args.db_host,
                        db_port=args.db_port,
                        udp_port=args.udp_port)
            except KeyboardInterrupt:
                logger.exception('CTRL+C hit.')
                com.close()
                client.close()
                sys.exit(0)

if __name__ == '__main__':
    main()