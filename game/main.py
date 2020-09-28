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
        self.dt = .1
        self.size = 200
        self.session_id = random.randint(1,1000)
        self.cache = redis.Redis(host='redis', port=6379)
        self.cache.hset(f'game{self.session_id}', 'alive', 'true')
        self.cache.hset(f'game{self.session_id}', 'x', 50)
        self.cache.hset(f'game{self.session_id}', 'y', 50)
        self.cache.hset(f'game{self.session_id}', 'vx', 0)
        self.cache.hset(f'game{self.session_id}', 'vy', 0)
        print(f'{self.session_id}>> WebSocket opened')
        a = self.cache.hget(f'game{self.session_id}', 'alive')
        print(a)

        async def client_loop():
            while True:
                if not self.cache.hget(f'game{self.session_id}', 'alive'):
                    print(f'  {self.session_id}>> Not alive :(')
                    break
                x = float(self.cache.hget(f'game{self.session_id}', 'x'))
                y = float(self.cache.hget(f'game{self.session_id}', 'y'))
                self.write_message(
                    f'update:{int(x)},{int(y)}'
                    )
                await tornado.gen.sleep(self.dt)

        async def game_loop():
            ps = self.cache.pubsub()
            ps.subscribe(f'input{self.session_id}')
            while True:
                if not self.cache.hget(f'game{self.session_id}', 'alive'):
                    print(f'  {self.session_id}>> Not alive :(')
                    break
                
                while True:
                    messages = ps.get_message()
                    if messages:
                        print(f'{self.session_id}>> ', messages.get('data'))  

                        msg = messages.get('data')
                        if msg == b'left':
                            vy = float(self.cache.hget(f'game{self.session_id}', 'vy'))
                            vy = vy-1
                            self.cache.hset(f'game{self.session_id}', 'vy', vy)
                        if msg == b'right':
                            vy = float(self.cache.hget(f'game{self.session_id}', 'vy'))
                            vy = vy+1
                            self.cache.hset(f'game{self.session_id}', 'vy', vy)
                    else: 
                        break

                x = float(self.cache.hget(f'game{self.session_id}', 'x'))
                y = float(self.cache.hget(f'game{self.session_id}', 'y'))
                vx = float(self.cache.hget(f'game{self.session_id}', 'vx'))
                vy = float(self.cache.hget(f'game{self.session_id}', 'vy'))
                x += vx * self.dt
                y += vy * self.dt
                if y < 0:
                    y = -y
                    self.cache.hset(f'game{self.session_id}', 'vy', -vy*.5)
                if y > self.size:
                    y = self.size * 2 - y
                    self.cache.hset(f'game{self.session_id}', 'vy', -vy*.5)
                self.cache.hset(f'game{self.session_id}', 'x', x)
                self.cache.hset(f'game{self.session_id}', 'y', y)
                print(f'{self.session_id}>>', x, y, vx, vy)

                await tornado.gen.sleep(self.dt)

        tornado.ioloop.IOLoop.current().spawn_callback(client_loop)
        tornado.ioloop.IOLoop.current().spawn_callback(game_loop)
        print(f'{self.session_id}>> open end')

    def on_message(self, message):
        print(f'{self.session_id}>> recieved: ' + message)
        self.write_message(u'You said: ' + message)

        if message == 'left':
            self.cache.publish(f'input{self.session_id}', 'left')
        if message == 'right':
            self.cache.publish(f'input{self.session_id}', 'right')

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
