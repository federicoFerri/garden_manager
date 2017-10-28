#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import garden_router

class Serve(object):
    def __init__(self, config):
        self.config = config
        self.garden_router = garden_router.GardenRouter(config)

    def enable(self, getvars):
        return self.garden_router.enable()

    def disable(self, getvars):
        return self.garden_router.disable()

    def ping(self, getvars):
        if 'device' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain device field'}
        return self.garden_router.ping(getvars['device'][0])

    def read(self, getvars):
        if 'device' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain device field'}
        if 'pin' not in getvars.keys():
            return {'success': False, 'error': 'Query string must contain pin field'}
        return self.garden_router.read(getvars['device'][0], getvars['pin'][0])

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