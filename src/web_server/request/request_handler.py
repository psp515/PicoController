from logging.logger import Logger
from web_server.request.request import Request


class RequestHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, 'initialized', False):
            self.initialized = True
            self.logger = Logger()
            self.gets = {}
            self.posts = {}
            self.unhandled_request_response = "HTTP/1.1 404 Not Found\r\n\r\n"

    async def handle_request(self, reader, writer):
        try:
            raw = await reader.readline()
            request = Request(raw)

            self.logger.info(f"Request path: {request.url}")
            self.logger.debug(f"Full request: {raw}")

            response = await self._get_response(request)

            writer.write(response.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            writer.write("HTTP/1.1 500 Internal Server Error\r\n\r\n".encode('utf-8'))
        finally:
            await writer.drain()
            await writer.wait_closed()

    def map_get(self, path: str, callback):
        if path in self.gets:
            raise Exception(f"Path {path} already mapped.")

        self.gets[path] = callback

    def map_post(self, path: str, callback):
        if path in self.posts:
            raise Exception(f"Path {path} already mapped.")

        self.posts[path] = callback

    def set_unhandled_request_response(self, response: str):
        self.unhandled_request_response = response

    async def _get_response(self, request: Request):

        if request.method == 'GET':
            return self.gets[request.url](request)

        if request.method == 'POST':
            return self.posts[request.url](request)

        return self.unhandled_request_response
