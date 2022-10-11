# - *- coding: utf- 8 - *-

import logging
import serial

logging.basicConfig(
    # format='%(levelname)s:%(message)s',
    format='[%(asctime)s] %(pathname)s:%(lineno)d %(levelname)s - %(message)s',
    level=logging.DEBUG,
)

status_codes = {
    '*': 'command successfully executed',
    '#': 'command not executed',
    '-': 'negative response',
    '+': 'positive response',
}


class ImatecPump(object):
    '''
    This interface is based on
    https://pim-resources.coleparmer.com/instruction-manual/14-036-e-ismatec-reglo-icc-english-revc.pdf
    '''
    def __init__(self, port):
        # setup a connection to the pump
        self.serial_connection = serial.Serial(port, timeout=2)
        logging.info('Established a connection to pump at %s' % port)

        self._send('O')
        logging.debug(
            'Change Mode to Volume over Time: %s' % (
                status_codes[self._readline()]
            )
        )
        self._send('xM')
        logging.debug('mode of the pump: %s' % self._readline())
        self.set_direction_counter_clockwise()

    @staticmethod
    def parse_volume_type_one_two_to_float(encoding):
        float_str = '%s.%se%s' % (encoding[0], encoding[1:4], encoding[-2:])
        return float(float_str) / 1e3

    @staticmethod
    def float_to_volume_type_two(value):
        exp_encoding = '%5.3E' % (value * 1e3)
        return (
            exp_encoding[0]
            + exp_encoding[2:5]
            + exp_encoding[-3]
            + exp_encoding[-1]
        )

    def set_direction_clockwise(self):
        self._send('J')
        response = self._readline()
        logging.info('Set direction to clockwise: %s' % status_codes[response])
        return response

    def set_direction_counter_clockwise(self):
        self._send('K')
        response = self._readline()
        logging.info(
            'Set direction to counter-clockwise: %s' % status_codes[response]
        )
        return response

    def get_volume(self):
        self._send("v")
        return self._readline()

    def set_volume(self, volume):
        """
        100myL => 1000-1
        """
        # if volume > 9999:
        #     raise ValueError('too much volume')

        self._send('v%s' % self.float_to_volume_type_two(volume))
        logging.info('Set volume to %s uL' % volume)
        logging.debug(self._readline())

    def get_flow_rate(self):
        self._send('f')
        return self._readline()

    def set_flow_rate(self, rate):
        if rate > 2e3:
            raise ValueError('flow rate is too high')

        self._send('f%s' % self.float_to_volume_type_two(rate))
        logging.info('Set volume to %s uL / min' % rate)
        response = self._readline()
        logging.debug(response)
        return response

    def start(self):
        self._send("H")
        reponse = self._readline()
        logging.debug('response: %s' % reponse)
        if '-' in reponse:
            self._send('xe')
            logging.debug(self._readline())
        return reponse

    def stop(self):
        self._send("I")
        return self._readline()

    def _readline(self):
        if self.serial_connection.in_waiting == 1:
            return self.serial_connection.read().decode("utf-8")
        else:
            return self.serial_connection.read_until().decode("utf-8")

    def _send(self, message, adress=1):
        command = '%s%s\r\n' % (adress, message)
        logging.debug(command)
        self.serial_connection.write(command.encode())

    def get_mode(self):
        self._send('xM')
        response = self._readline()
        logging.info("Pump mode is: " + response)
        return response

    def set_mode(self, mode="O"):
        self._send(mode)
        logging.debug(self._readline())
