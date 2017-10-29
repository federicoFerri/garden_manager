#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyA20.gpio import gpio
from pyA20.gpio import port
import serial
import struct
import rs485
import time

class GardenRouter():
    def __init__(self, config):
        self.config = config

        self.relay = port.PA11
        self.rs485_enable = port.PA12

        gpio.init()
        gpio.setcfg(self.relay, gpio.OUTPUT)
        gpio.output(self.relay, 1)
        gpio.setcfg(self.rs485_enable, gpio.OUTPUT)
        gpio.output(self.rs485_enable, 0)

        serial_port = serial.Serial(self.config.get('serial', 'port'), baudrate=57600, timeout=0)
        self.rs485 = rs485.SerialWrapper(serial_port)

        self.devices = {}
        for device, pins in self.config.items('devices'):
            self.devices[int(device)] = list(map(int, pins.split(',')))

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
        message = bytes([device, 2, 0, 0])
        gpio.output(self.rs485_enable, 1)
        self.rs485.sendMsg(message)
        time.sleep(float(self.config.get('serial', 'delay')))
        gpio.output(self.rs485_enable, 0)
        s = time.time()
        while True:
            if self.rs485.update():
                packet = self.rs485.getPacket()
                data = struct.unpack('3B',packet)
                if data[0:2] == (0,1):
                    return {'success': True, 'data': None}
                return {'success': False, 'error': 'Invalid response from device'}
            if time.time() - s > int(self.config.get('serial', 'timeout')):
                return {'success': False, 'error': 'Device not responding, timeout'}

    def read(self, device, pin):
        if not self.enabled:
            return {'success': False, 'error': 'You must enable it first'}
        device = int(device)
        pin = int(pin)
        if not device in self.devices:
            return {'success': False, 'error': 'Invalid device'}
        if not pin in self.devices[device]:
            return {'success': False, 'error': 'Invalid device pin'}
        message = bytes([device, 0, pin, 0])
        gpio.output(self.rs485_enable, 1)
        self.rs485.sendMsg(message)
        time.sleep(float(self.config.get('serial', 'delay')))
        gpio.output(self.rs485_enable, 0)
        s = time.time()
        while True:
            if self.rs485.update():
                packet = self.rs485.getPacket()
                data = struct.unpack('3B',packet)
                return {'success': True, 'data': (data[1] << 8) + data[2]}
            if time.time() - s > int(self.config.get('serial', 'timeout')):
                return {'success': False, 'error': 'Device not responding, timeout'}

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
        message = bytes([device, 1, pin, value])
        gpio.output(self.rs485_enable, 1)
        self.rs485.sendMsg(message)
        time.sleep(float(self.config.get('serial', 'delay')))
        gpio.output(self.rs485_enable, 0)
        s = time.time()
        while True:
            if self.rs485.update():
                packet = self.rs485.getPacket()
                data = struct.unpack('3B', packet)
                if data[0:2] == (0,1):
                    return {'success': True, 'data': None}
                return {'success': False, 'error': 'Invalid response from device, pin is not valid'}
            if time.time() - s > int(self.config.get('serial', 'timeout')):
                return {'success': False, 'error': 'Device not responding, timeout'}