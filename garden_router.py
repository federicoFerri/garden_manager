#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyA20.gpio import gpio
from pyA20.gpio import port
import serial
import struct
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

        max_pin = []
        min_pin = []
        self.devices = {}
        for device, pins in self.config.items('devices'):
            self.devices[int(device)] = list(map(int, pins.split(',')))
            max_pin.append(max(self.devices[int(device)]))
            min_pin.append(min(self.devices[int(device)]))

        self.scan_list = []
        for pin in range(min(min_pin), max(max_pin) + 1):
            for device, pins in self.devices.items():
                if pin in pins:
                    self.scan_list.append((device, pin))

        self.enabled = False

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
        if not device in self.devices:
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
        if not device in self.devices:
            return {'success': False, 'error': 'Invalid device'}
        if not pin in self.devices[device]:
            return {'success': False, 'error': 'Invalid device pin'}
        time.sleep(self.delay)
        message = bytes([device, 0, pin, 0])
        self.conn.write(message)
        response = self.conn.read(size=5)
        if response == b'':
            return {'success': False, 'error': 'Device not responding, timeout'}
        data = struct.unpack('5B',response)
        return {'success': True, 'data': (data[1] << 8) + data[2]}

    def write(self, device, pin, value):
        if not self.enabled:
            return {'success': False, 'error': 'You must enable it first'}
        device = int(device)
        pin = int(pin)
        value = int(value)
        if not device in self.devices:
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