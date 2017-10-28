#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse import urlparse, parse_qs
from logging.config import fileConfig
import api_dispatch
import configparser
import http.server
import socketserver
import logging
import sys
import os
import ssl
import base64
import json

config = configparser.ConfigParser()
config.read('config/main.conf')

class CustomServerHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="%s"' % config.get('api', 'name'))
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        logger.info('GET %s - %s' % (self.path, self.client_address[0]))
        key = self.server.get_auth_key()
        ''' Present frontpage with user authentication. '''
        if self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
            logger.warning('No auth header received %s' % self.client_address[0])
            response = {'success': False,'error': 'No auth header received'}
            self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        elif self.headers.get('Authorization') == 'Basic ' + str(key):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            getvars = self._parse_GET()
            base_path = urlparse(self.path).path
            try:
                fnc = getattr(self.api_dispatch, base_path[1:])
                try:
                    response = fnc(getvars)
                    self.wfile.write(bytes(json.dumps(response), 'utf-8'))
                except Exception as e:
                    logger.exception("There was an exception in %s" % fnc.__name__)
                    logger.debug(e)
                    response = {'success': False, 'error': 'Internal error'}
                    self.wfile.write(bytes(json.dumps(response), 'utf-8'))
            except:
                response = {'success': False, 'error': 'Resource not found'}
                self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        else:
            self.do_AUTHHEAD()
            logger.warning('Invalid credentials %s' % self.client_address[0])
            response = {'success': False,'error': 'Invalid credentials'}
            self.wfile.write(bytes(json.dumps(response), 'utf-8'))

    def _parse_GET(self):
        getvars = parse_qs(urlparse(self.path).query)
        return getvars

class CustomHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    key = ''

    def __init__(self, address, handlerClass=CustomServerHandler):
        handlerClass.api_dispatch = api_dispatch.Serve(config)
        super().__init__(address, handlerClass)

    def set_auth(self, username, password):
        self.key = base64.b64encode(bytes('%s:%s' % (username, password), 'utf-8')).decode('ascii')

    def get_auth_key(self):
        return self.key

def start_webserver():
    logger.info('Starting API interface %s:%s' % (config.get('host', 'name'), config.get('host', 'port')))
    server = CustomHTTPServer((config.get('host', 'name'), int(config.get('host', 'port'))))
    server.set_auth(config.get('api', 'user'), config.get('api', 'password'))
    server.socket = ssl.wrap_socket(server.socket, server_side=True, certfile=config.get('cert', 'file'),ssl_version=ssl.PROTOCOL_TLSv1_2)
    server.serve_forever()

if __name__ == '__main__':
    if not os.getegid() == 0:
        sys.exit('Must be run as root')

    fileConfig(config.get('logging', 'file'))
    logger = logging.getLogger('main')
    logger.info('Starting application')
    start_webserver()