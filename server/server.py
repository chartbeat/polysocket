import json
import os

from tornado import ioloop
from tornado.template import Loader
from tornado.web import Application
from tornado.web import RequestHandler
from tornado.web import StaticFileHandler
from tornado.websocket import WebSocketHandler

SOCKETS = set()

class PolySocketHandler(WebSocketHandler):
    def open(self):
        SOCKETS.add(self)

    def on_close(self):
        SOCKETS.remove(self)

    def on_message(self, message):
        # self.write_message(response)
        print message

class CommandHandler(RequestHandler):
    def prepare(self):
        """
        Create an easily accessible JSON map of post data
        """
        content_type = self.request.headers.get('Content-Type', '')
        if content_type.startswith('application/json'):
            self.arguments = json.loads(self.request.body)

    def post(self):
        command = self.arguments.get('cmd')
        wrapped = '(function(){%s})()' % command
        print 'Running command on %d hosts: %s' % (len(SOCKETS), wrapped)
        for socket in SOCKETS:
            socket.write_message(wrapped)

class StatsHandler(RequestHandler):
    def get(self):
        data = {
            'connections': len(SOCKETS),
        }

        self.write(json.dumps(data))

class WebUIHandler(RequestHandler):
    loader = Loader(os.path.join(os.getcwd(), 'templates'))

    def get(self):
        template = self.loader.load('webui.html').generate()
        self.write(template)
        
application = Application([
    (r'/', WebUIHandler),
    (r'/cmd/', CommandHandler),
    (r'/_socket/', PolySocketHandler),
    (r'/static/(.*)', StaticFileHandler, { 'path': os.path.join(os.getcwd(), 'static') }),
    (r'/stats/', StatsHandler),
])

if __name__ == '__main__':
    application.listen(8888)
    ioloop.IOLoop.instance().start()
