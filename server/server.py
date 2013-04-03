import asyncmongo
import json
import logging
import os
import uuid

from argparse import ArgumentParser
from tornado import ioloop
from tornado.web import Application
from tornado.web import HTTPError
from tornado.web import RequestHandler
from tornado.web import StaticFileHandler
from tornado.web import asynchronous
from tornado.websocket import WebSocketHandler

SOCKETS = set()
CONTROLS = {}
VERSION = 0.1

SETTINGS = {}

BANNER = """
              _                      _        _   
             | |                    | |      | |  
  _ __   ___ | |_   _ ___  ___   ___| | _____| |_ 
 | '_ \ / _ \| | | | / __|/ _ \ / __| |/ / _ \ __|
 | |_) | (_) | | |_| \__ \ (_) | (__|   <  __/ |_ 
 | .__/ \___/|_|\__, |___/\___/ \___|_|\_\___|\__|
 | |             __/ |                        v{version}
 |_|            |___/                             
""".format(version=VERSION)

def parse_master(message):
    """
    Given a message in the form of "[master]{response}", parse out the master and the response
    @param str: message, The message from the client
    @return (str, str), The master socket to message and the response to send
    """
    results = message.split(']')
    results[0] = results[0].replace('[', '')
    return (results[0], results[1])

def wrap_output(master, message):
    return '[%s](function(){%s})()' % (master, message)

def parse_command_line():
    parser = ArgumentParser(description='Polysocket server')
    parser.add_argument('--port', dest='port', metavar='p', type=int, default='8888', help='The port to run the server on')
    parser.add_argument('--mongo-server', dest='mongo_server', type=str, default='127.0.0.1', help='The location of the mongo server')
    parser.add_argument('--mongo-port', dest='mongo_port', type=int, default=27017, help='The port the mongo server is listening on')
    return parser.parse_args()

class PolySocketHandler(WebSocketHandler):
    def open(self):
        SOCKETS.add(self)

    def on_close(self):
        SOCKETS.remove(self)

    def on_message(self, message):
        master, response = parse_master(message)
        CONTROLS[master].write_message(response)

class MasterSocketHandler(WebSocketHandler):
    def open(self):
        self.uuid = str(uuid.uuid4())
        CONTROLS[self.uuid] = self
        logging.getLogger('polysocket').info('Opened master connection: %s' % self.uuid)

    def on_close(self):
        del CONTROLS[self.uuid]

    def on_message(self, message):
        wrapped = wrap_output(self.uuid, message)
        for socket in SOCKETS:
            socket.write_message(wrapped)

class StatsHandler(RequestHandler):
    def get(self):
        data = {
            'slaves': len(SOCKETS),
            'masters': len(CONTROLS),
        }

        self.write(json.dumps(data))

class WebUIHandler(RequestHandler):
    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = asyncmongo.Client(pool_id='polysocket', host=SETTINGS.mongo_server,
                                         port=SETTINGS.mongo_port, maxcached=10, maxconnections=50, dbname='polysocket')
        return self._db

    @property
    def templates_dir(self):
        if not hasattr(self, '_templates_dir'):
            self._templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        return self._templates_dir

    @asynchronous
    def get(self):
        self.db.programs.find(callback=self._on_complete)

    def _on_complete(self, response, error):
        if error:
            raise HTTPError(500)
        self.render(os.path.join(self.templates_dir, 'webui.html'), programs=response)
        
application = Application([
    (r'/', WebUIHandler),
    (r'/master/', MasterSocketHandler),
    (r'/_socket/', PolySocketHandler),
    (r'/static/(.*)', StaticFileHandler, { 'path': os.path.join(os.getcwd(), 'static') }),
    (r'/stats/', StatsHandler),
])

if __name__ == '__main__':
    SETTINGS = parse_command_line()
    log_format = '[%(asctime)s] %(message)s'
    logging.basicConfig(format=log_format)
    logger = logging.getLogger('polysocket')
    logger.setLevel(logging.INFO)
    print BANNER
    logger.info('Server running at 127.0.0.1:{port}'.format(port=SETTINGS.port))
    logger.info('MongoDB connection is at {server}:{port}'.format(server=SETTINGS.mongo_server, port=SETTINGS.mongo_port))
    try:
        application.listen(SETTINGS.port)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
