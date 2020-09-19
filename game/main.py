import tornado.websocket
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print('dupa')
        # self.write("Hello, world")
        self.render("template.html", title="My title", items=['hello!', '2nd', '3'])

class TestSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", TestSocketHandler),
    ], autoreload=True)

if __name__ == "__main__":
    print('(re)starting')
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()