#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyA20.gpio import gpio
from pyA20.gpio import port
import serial
import struct
import json
import time

class GardenRouter():
    def __init__(self, config):
        self.config = config

        self.relay = port.PA11

        gpio.init()
        gpio.setcfg(self.relay, gpio.OUTPUT)
        gpio.output(self.relay, 1)

        self.delay = self.config.getfloat('serial', 'delay')
        baudrate = self.config.getint('serial', 'baudrate')
        timeout = self.config.getint('serial', 'timeout')
        self.conn = serial.Serial(self.config.get('serial', 'port'), baudrate=baudrate, timeout=timeout)

        with open(self.config.get('devices', 'file')) as f:
            self.devices_data = json.load(f)

        all_pins = []
        for device, pins in self.devices.items():
            all_pins += pins
        self.scan_list = []
        for pin in range(min(all_pins), max(all_pins) + 1):
            for device, pins in self.devices.items():
                if pin in pins:
                    self.scan_list.append((device, pin, self.data_types[device][pin]))

        self.enabled = False

    def _is_device_valid(self, device):
        return any((True for device_data in self.devices_data if device_data['device'] == device))

    def get_device_name(self, device):
        return next((device_data['name'] for device_data in self.devices_data if device_data['device'] == device), None)

    def _is_pin_valid(self, device, pin):
        pins_data = next((device_data['pins'] for device_data in self.devices_data if device_data['device'] == device), [])
        return any((True for pin_data in pins_data if pin_data['device'] == pin))

    def get_pin_name(self, device, pin):
        pins_data = next((device_data['pins'] for device_data in self.devices_data if device_data['device'] == device), [])
        return next((pin_data['name'] for pin_data in pins_data if pin_data['device'] == pin), None)

    def get_read_all_list(self):
        scan_list = []
        for device_data in self.devices_data:
            scan_list += [(device_data['device'], pin_data['pin']) for pin_data in device_data['pins']]
        return sorted(scan_list, key=lambda x: (x[1], x[0]))

    def get_ping_all_list(self):
        return [device_data['device'] for device_data in self.devices_data]

    def _decode(self, device, pin, data):
        pins_data = next((device_data['pins'] for device_data in self.devices_data if device_data['device'] == device), [])
        data_type = next((pin_data['data_type'] for pin_data in pins_data if pin_data['device'] == pin), None)
        if data_type == '16bit_int':
            return struct.unpack('H', data[1:3])
        elif data_type == '32bit_float':
            return struct.unpack('<f', data[1:5])
        else:
            return None

    def enable(self):
        gpio.output(self.relay, 0)
        time.sleep(1)
        self.enabled = True
        return {'success': True, 'data': None}

    def disable(self):
        gpio.output(self.relay, 1)
        time.sleep(1)
        self.enabled = False
        return {'success': True, 'data': None}

    def ping(self, device):
        if not self.enabled:
            return {'success': False, 'error': 'You must enable it first'}
        device = int(device)
        if not self._is_device_valid(device):
            return {'success': False, 'error': 'Invalid device'}
        time.sleep(self.delay)
        s = time.time()
        message = bytes([device, 2, 0, 0])
        self.conn.write(message)
        response = self.conn.read(size=5)
        if response == b'':
            return {'success': False, 'error': 'Device not responding, timeout'}
        data = struct.unpack('5B',response)
        if data[0:2] == (0,1):
            return {'success': True, 'data': {'time': time.time() - s}}
        return {'success': False, 'error': 'Invalid response from device'}

    def read(self, device, pin):
        if not self.enabled:
            return {'success': False, 'error': 'You must enable it first'}
        device = int(device)
        pin = int(pin)
        if not self._is_device_valid(device):
            return {'success': False, 'error': 'Invalid device'}
        if not self._is_pin_valid(device, pin):
            return {'success': False, 'error': 'Invalid device pin'}
        time.sleep(self.delay)
        message = bytes([device, 0, pin, 0])
        self.conn.write(message)
        response = self.conn.read(size=5)
        if response == b'':
            return {'success': False, 'error': 'Device not responding, timeout'}
        return {'success': True, 'data': self._decode(device, pin, response)}

    def write(self, device, pin, value):
        if not self.enabled:
            return {'success': False, 'error': 'You must enable it first'}
        device = int(device)
        pin = int(pin)
        value = int(value)
        if not self._is_device_valid(device):
            return {'success': False, 'error': 'Invalid device'}
        if not pin in range(0,256):
            return {'success': False, 'error': 'Invalid device pin, out of byte range'}
        if not value in range(0,256):
            return {'success': False, 'error': 'Invalid value, out of byte range'}
        time.sleep(self.delay)
        message = bytes([device, 1, pin, value])
        self.conn.write(message)
        response = self.conn.read(size=5)
        if response == b'':
            return {'success': False, 'error': 'Device not responding, timeout'}
        data = struct.unpack('5B', response)
        if data[0:2] == (0,1):
            return {'success': True, 'data': None}
        return {'success': False, 'error': 'Invalid response from device, pin is not valid'}