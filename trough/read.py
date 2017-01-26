#!/usr/bin/env python3
from bin.settings import settings
import sqlite3
import ujson
import os
import sqlparse
import logging

# TODO: Refactor to class 'ReadServer'

class ReadServer:
    def __init__(segment_path):
        self.connection = sqlite3.connect(segment_path)
        self.cursor = self.connection.cursor()

    def stream_output(self, start_response):
        first = True
        try:
            for row in self.cursor.execute(query.decode('utf-8')):
                if first:
                    start_response('200 OK', [('Content-Type','application/json')])
                    yield b"["
                if not first:
                    yield b","
                output = dict((self.cursor.description[i][0], value) for i, value in enumerate(row))
                yield ujson.dumps(output).encode('utf-8')
                first = False
            yield b"]"
        except Exception as e:
            start_response('500 Server Error', [('Content-Type', 'text/plain')])
            yield [b'500 Server Error: %s' % str(e).encode('utf-8')]
        self.cursor.close()
        self.cursor.connection.close()

    def read(query, start_response):
        logging.info('Servicing request: {query}'.format(query=query))
        # if the user sent more than one query, or the query is not a SELECT, raise an exception.
        if len(sqlparse.split(query)) != 1 or sqlparse.parse(query)[0].get_type() != 'SELECT':
            raise Exception('Exactly one SELECT query per request, please.')
        return self.stream_output(start_response)

def application(env):
    try:
        segment_name = env.get('HTTP_HOST', "").split(".")[0] # get database id from host/request path
        segment_path = os.path.join(settings['LOCAL_DATA'], "{name}.sqlite".format(name=segment_name))
        query = env.get('wsgi.input').read()
        return ReadServer(segment_path).read(query, start_response)
    except Exception as e:
        start_response('500 Server Error', [('Content-Type', 'text/plain')])
        return [b'500 Server Error: %s' % str(e).encode('utf-8')]