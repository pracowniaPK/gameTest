import os
import time
import random

import redis
import tornado.gen
import tornado.websocket
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print('dupa           ')
        # self.write("Hello, world")
        self.cache = redis.Redis(host='redis', port=6379)
        count = self.get_hit_count()
        print(count)
        self.render("template.html", title="My title", items=['hello!', str(count), '🤷'])

    def get_hit_count(self):
        retries = 5
        while True:
            try:
                return self.cache.incr('hits')
            except redis.exceptions.ConnectionError as exc:
                if retries == 0:
                    raise exc
                retries -= 1
                time.sleep(0.5)

class TestSocketHandler(tornado.websocket.WebSocketHandler):
    async def open(self):
        self.session_id = random.randint(1,1000)
        print(f'{self.session_id}>> WebSocket opened')

        async def my_loop():
            while True:
                await tornado.gen.sleep(5)
                print(f'{self.session_id}>> i\'still alive')

        tornado.ioloop.IOLoop.current().spawn_callback(my_loop)
        print(f'{self.session_id}>> open end')

    def on_message(self, message):
        print(f'{self.session_id}>> recieved: ' + message)
        self.write_message(u'You said: ' + message)

    def on_close(self):
        print(f'{self.session_id}>> WebSocket closed')

    def check_origin(self, origin):
        return True

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws/", TestSocketHandler),
        (r"/static/", tornado.web.StaticFileHandler, {'path': 'static_files'}),
    ], autoreload=True,
    static_path='static')

if __name__ == "__main__":
    print('(re)starting')
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
