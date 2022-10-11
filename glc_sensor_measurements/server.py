import csv
import datetime
import logging
import os
import re
import serial
import time

import glc_sensor_measurements.gRPC_command_center as gRPC_command_center
from glc_sensor_measurements.pump import ImatecPump


class GlucoseSensorServicer(
    gRPC_command_center.GlucoseSensorServicer
):
    def establish_pump_connection(self, port):
        self.pump = ImatecPump(port)

    def establish_sensor_connection(self, port):
        self.sensor = serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

    def set_storage_location(self, path):
        self.storage_location = path

    def record_measurements_forever(self):
        # remove old messages
        self.last_value = {}
        [one for one in self.sensor.readline()]

        reg_pattern = re.compile(
            r'(\d+);([-\d]+)'
        )
        self.all_measurements_path = os.path.join(
            self.storage_location,
            'measurement_recording_%s.csv' % (
                datetime.datetime.now().isoformat()
            )
        )

        # write the header
        with open(self.all_measurements_path, 'w') as csv_file:
            csv.writer(csv_file).writerow(
                [
                    'Time',
                    'Glucose Current [nA]',
                    'Lactate Current [nA]',
                ]
            )
        logging.info('Recording measurements in file %s' % csv_file)
        while True:
            pure_message = self.sensor.readline().decode('utf-8')
            logging.debug(pure_message)
            result = reg_pattern.findall(pure_message)
            if len(result) > 0:
                glc_value, lactate_value = result[0]
                timestamp = datetime.datetime.now().isoformat()
                with open(self.all_measurements_path, 'a') as csv_file:
                    csv.writer(csv_file).writerow((
                        timestamp,
                        float(glc_value),
                        float(lactate_value),
                    ))
                self.last_value = {
                    'timestamp': timestamp,
                    'glucose_current': float(glc_value),
                    'lactate_current': float(lactate_value),
                }
            else:
                continue

    def pump_it_up(self, request, context):
        self.pump.set_volume(request.volume)
        logging.info(self.pump.set_flow_rate(request.flow_rate))
        logging.debug(self.pump.start())
        return gRPC_command_center.VolumeResponse(
            duration=request.volume / request.flow_rate
        )

    def monitor(self, request, context):
        start = time.time()
        last_observation = {}
        while (time.time() - start) / 60 < request.duration:
            if last_observation != self.last_value:
                yield gRPC_command_center.Measurement(**self.last_value)
                last_observation = self.last_value
            else:
                time.sleep(1)

    def record(self, request, context):
        file_name = os.path.join(
            self.storage_location,
            '%s_%s.csv' % (request.name, datetime.datetime.now().isoformat())
        )
        # write the header
        with open(file_name, 'w') as csv_file:
            csv.writer(csv_file).writerow(
                [
                    'Time',
                    'Glucose Current [nA]',
                    'Glucose Concentration [g/L]',
                    'Lactate Current [nA]',
                    'Lactate Concentration [g/L]',
                ]
            )
        start = time.time()
        logging.info(
            'Start Recording the Sensor for %3d minute(s)' % request.duration
        )
        last_observation = {}
        while (time.time() - start) / 60 < request.duration:
            if last_observation != self.last_value:
                with open(file_name, 'a') as csv_file:
                    csv.writer(csv_file).writerow((
                        self.last_value['timestamp'],
                        self.last_value['glucose_current'],
                        request.real_glucose,
                        self.last_value['lactate_current'],
                        request.real_lactate,
                    ))
                yield gRPC_command_center.Measurement(**self.last_value)
                last_observation = self.last_value
            else:
                time.sleep(1)
