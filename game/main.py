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
        print('dupa          ')
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
        self.cache = redis.Redis(host='redis', port=6379)
        self.cache.hset(f'game{self.session_id}', 'alive', 'true')
        self.cache.hset(f'game{self.session_id}', 'x', 50)
        self.cache.hset(f'game{self.session_id}', 'y', 50)
        print(f'{self.session_id}>> WebSocket opened')
        a = self.cache.hget(f'game{self.session_id}', 'alive')
        print(a)

        async def my_loop():
            while True:
                if not self.cache.hget(f'game{self.session_id}', 'alive'):
                    print(f'  {self.session_id}>> Not alive :(')
                    break
                x = int(self.cache.hget(f'game{self.session_id}', 'x'))
                y = int(self.cache.hget(f'game{self.session_id}', 'y'))
                print(f'{self.session_id}>> i\'still alive:', x, y)
                self.write_message(
                    f'update:{x},{y}'
                    )
                await tornado.gen.sleep(5)

        tornado.ioloop.IOLoop.current().spawn_callback(my_loop)
        print(f'{self.session_id}>> open end')

    def on_message(self, message):
        print(f'{self.session_id}>> recieved: ' + message)
        self.write_message(u'You said: ' + message)

        if message == 'left':
            y = int(self.cache.hget(f'game{self.session_id}', 'y'))
            y = max(0, y-5)
            self.cache.hset(f'game{self.session_id}', 'y', y)
            print('left', y)
        if message == 'right':
            y = int(self.cache.hget(f'game{self.session_id}', 'y'))
            y = min(100, y+5)
            self.cache.hset(f'game{self.session_id}', 'y', y)
            print('right', y)

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
