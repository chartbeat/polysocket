import json
import logging
import os
import uuid

from argparse import ArgumentParser
from tornado import ioloop
from tornado.template import Loader
from tornado.web import Application
from tornado.web import RequestHandler
from tornado.web import StaticFileHandler
from tornado.websocket import WebSocketHandler

SOCKETS = set()
CONTROLS = {}
VERSION = 0.1

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
    loader = Loader(os.path.join(os.getcwd(), 'templates'))

    def get(self):
        template = self.loader.load('webui.html').generate()
        self.write(template)
        
application = Application([
    (r'/', WebUIHandler),
    (r'/master/', MasterSocketHandler),
    (r'/_socket/', PolySocketHandler),
    (r'/static/(.*)', StaticFileHandler, { 'path': os.path.join(os.getcwd(), 'static') }),
    (r'/stats/', StatsHandler),
])

if __name__ == '__main__':
    args = parse_command_line()
    log_format = '[%(asctime)s] %(message)s'
    logging.basicConfig(format=log_format)
    logger = logging.getLogger('polysocket')
    logger.setLevel(logging.INFO)
    print BANNER
    logger.info('Server running at 127.0.0.1:{port}'.format(port=args.port))
    logger.info('No database connected')
    try:
        application.listen(args.port)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
