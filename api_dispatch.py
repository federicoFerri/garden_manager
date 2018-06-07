#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import garden_router
import time

class Serve(object):
    def __init__(self, config):
        self.config = config
        self.garden_router = garden_router.GardenRouter(config)
        self.users = 0

    def alloc(self, getvars):
        self.users += 1
        if self.users > 1:
            return {'success': True, 'data': None}
        return self.garden_router.enable()

    def free(self, getvars):
        self.users -= 1
        if self.users > 0:
            return {'success': True, 'data': None}
        return self.garden_router.disable()

    def ping(self, getvars):
        if 'device' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain device field'}
        return self.garden_router.ping(getvars['device'][0])

    def ping_all(self, getvars):
        data = {}
        for device in self.garden_router.devices:
            data[device] = self.garden_router.ping(device).get('data', None)
        return {'success': True, 'data': data}

    def read(self, getvars):
        if 'device' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain device field'}
        if 'pin' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain pin field'}
        return self.garden_router.read(getvars['device'][0], getvars['pin'][0])

    def read_all(self, getvars):
        data = {}
        for device, pin in self.garden_router.scan_list:
            if device not in data:
                data[device] = {}
            data[device][pin] = self.garden_router.read(device, pin).get('data', None)
        return {'success': True, 'data': data}

    def write(self, getvars):
        if 'device' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain device field'}
        if 'pin' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain pin field'}
        if 'value' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain value field'}
        return self.garden_router.write(getvars['device'][0], getvars['pin'][0], getvars['value'][0])

    def devices(self, getvars):
        return {'success': True, 'data': self.garden_router.devices}

    def scan_list(self, getvars):
        return {'success': True, 'data': self.garden_router.scan_list}