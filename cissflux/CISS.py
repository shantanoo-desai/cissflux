import sys
import time
import logging
import serial

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

class ciss:
    def __init__(self, device):
        """CISS Class to Extract Inertial Sensor Data. Default baudrate is 115200"""
        self.baudrate = 115200
        # range in us
        self.update_rate = range(500, 1000001)
        self.device = device
    
    def calc_crc(self, payload):
        """CRC Calculation"""
        eval = 0
        for i in payload:
            eval ^= i
        eval ^= 254
        return eval
    
    def write_conf(self, buffer_conf):
        """Write To Serial Port of the Sensor by appending CRC to the buffer before sending"""
        ser = serial.Serial(port=self.device, baudrate=self.baudrate, timeout=1)
        crc = self.calc_crc(buffer_conf)
        buffer_conf.append(crc)
        ser.write(buffer_conf)
        time.sleep(0.2)
        ser.close()
    
    def set_acc_range(self, resolution):
        """Set Accelerometer's Resolution. Valid values: 2, 4, 6, 8, 16 G. Default: 16G"""
        resolution_buffer = bytearray([0xfe, 0x3, 0x80, 0x4])
        if resolution not in [2, 4, 6, 8, 16]:
            print('given value not in range. Set to 16G')
            resolution_buffer.append(16)
        else:
            resolution_buffer.append(resolution)
        self.write_conf(resolution_buffer)
    
    def enable_sensor(self, id):
        """Enable Sensor by its ID"""
        cfg = bytearray([0xfe, 0x2])
        cfg.append(id)
        cfg.append(1)
        self.write_conf(cfg)
    
    def set_sampling(self, rate_in_us):
        """Set Sampling Rate (us). Default: 100ms"""
        ids = [0x80, 0x81, 0x82]
        for id in ids:
            frame = bytearray([0xfe, 0x6])
            frame.append(id)
            frame.append(2)
            if rate_in_us in self.update_rate:
                frame = frame + (rate_in_us).to_bytes(4, 'little')
            else:
                logger.debug('rate: {}'.format(rate_in_us))
                logger.info('update rate not within range. setting 100ms range')
                frame = frame + (100000).to_bytes(4, 'little')
            self.write_conf(frame)
            self.enable_sensor(id)
        
    def check_payload(self, incoming_data):
        """Check Incoming Payload via CRC Check"""
        checksum = incoming_data.pop()
        logger.debug(checksum)
        eval = 0
        for i in incoming_data:
            eval ^= i
        if eval == checksum:
            return True
        else:
            return False
    
    def s16(self, value):
        """Signed 16-bit Value Conversion"""
        return - (value & 0x8000) | (value & 0x7fff)


    def parse_inert_vec(self, data):
        """Extract and return the X,Y,Z Axes Inertial Vector values"""
        x = self.s16(data[0] | (data[1] << 8))
        y = self.s16(data[2] | (data[3] << 8))
        z = self.s16(data[4] | (data[5] << 8))
        array = [x, y, z]
        return array
    
    def parse_payload(self, accepted_data):
        """Parse the Accepted Payload for Different Sensors Values and return extracted data"""
        logger.debug(accepted_data)
        accepted_data.pop(0)  # remove length
        data_length = 6  # for inertial
        extracted_data = []
        while len(accepted_data) != 0:
            data_type = {'measurement': '', 'fields':{'x': 0.0, 'y': 0.0, 'z': 0.0}}
            if accepted_data[0] == 2:
                logger.info('type: acc')
                data_type['measurement'] = 'acc'
                accepted_data.pop(0)
                if len(accepted_data) < data_length:
                    break
                res = self.parse_inert_vec(accepted_data[0:data_length])
                data_type['fields']['x'], data_type['fields']['y'], data_type['fields']['z'] = [v/1000 for v in res]
                logger.debug(data_type)
                extracted_data.append(data_type)
                accepted_data = accepted_data[data_length:]

            elif accepted_data[0] == 3:
                logger.info('type: mag')
                data_type['measurement'] = 'mag'
                accepted_data.pop(0)
                if len(accepted_data) < data_length:
                    break
                res = self.parse_inert_vec(accepted_data[0:data_length])
                # res = self.parse_inert_vec(list(accepted_data))
                data_type['fields']['x'], data_type['fields']['y'], data_type['fields']['z'] = res
                logger.debug(data_type)
                extracted_data.append(data_type)
                accepted_data = accepted_data[data_length:]

            elif accepted_data[0] == 4:
                logger.info('type: gyro')
                data_type['measurement'] = 'gyro'
                accepted_data.pop(0)
                if len(accepted_data) < data_length:
                    break
                res = self.parse_inert_vec(accepted_data[0:data_length])
                # res = self.parse_inert_vec(list(accepted_data))
                data_type['fields']['x'], data_type['fields']['y'], data_type['fields']['z'] = res
                logger.debug(data_type)
                extracted_data.append(data_type)
                accepted_data = accepted_data[data_length:]

            elif accepted_data[0] == 1:
                accepted_data.pop(0)
                logger.info('type: enable')
                logger.debug('"sensor:" {}, "ack", "setup: {}"'.format(hex(accepted_data[0]), hex(accepted_data[1])))
                accepted_data = accepted_data[data_length:]
        
        return extracted_data


    def disable_all_sensors(self):
        """Disable All sensors (recommended before initialization)"""
        DISABLE_SENSORS = {
            'acc': bytearray([0xfe, 0x2, 0x80, 0x0]),
            'mag': bytearray([0xfe, 0x2, 0x81, 0x0]),
            'gyro': bytearray([0xfe, 0x2, 0x82, 0x0]),
            'env': bytearray([0xfe, 0x2, 0x83, 0x0]),
            'light': bytearray([0xfe, 0x2, 0x84, 0x0])
        }
        for sensor in DISABLE_SENSORS:
            logger.debug('Disabling {}'.format(sensor))
            self.write_conf(DISABLE_SENSORS[sensor])


        



