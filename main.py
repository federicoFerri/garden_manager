import os
import sys
from ConfigParser import ConfigParser
from time import sleep
from pyA20.gpio import gpio, port
import serial
import rs485

class GardenManager():
    def __init__(self):
        self.relay = port.PA11
        self.rs485_enable = port.PA12

        gpio.init()
        gpio.setcfg(self.relay, gpio.OUTPUT)
        gpio.output(self.relay, 1)
        gpio.setcfg(self.rs485_enable, gpio.OUTPUT)
        gpio.output(self.rs485_enable, 0)
        port = serial.Serial(config['serial']['port'], baudrate=57600, timeout=0, rtscts=True)
        self.rs485 = rs485.SerialWrapper(port)
        self.devices = {}
        for device in config['devices']:
            self.devices[int(device)] = list(map(int, config['devices'][device].split(',')))
        self.enabled = False

    def read(self, device, pin):
        if self.enabled:
            device = int(device)
            pin = int(pin)
            if device in self.devices and pin in self.devices[device]:
                message = bytearray([device, 0, pin, 0])
                gpio.output(self.rs485_enable, 1)
                self.rs485.sendMsg(message)
                gpio.output(self.rs485_enable, 0)
                while True:
                    if self.rs485.update():
                        packet = self.rs485.getPacket()
                        print(len(packet), " bytes received\n".encode())
                        print(packet)
        return False


if __name__ == '__main__':
    if not os.getegid() == 0:
        sys.exit('Script must be run as root')
    config = ConfigParser()
    config.read('main.conf')

    gm = GardenManager()

    try:
        print ("Press CTRL+C to exit")
        while True:
            gpio.output(relay, 0)
            sleep(1000)
    except KeyboardInterrupt:
        print ("Goodbye.")