from utils.logger import Logger

from configuration_server.request.enums.status_code import StatusCode
from configuration_server.request.request import Request
from configuration_server.request.response import Response


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
            first_line = await reader.readline()
            self.logger.debug(f"Full request: {first_line}")

            if not first_line:
                raise Exception("Empty request.")

            # Read headers
            headers = {}
            while True:
                line = await reader.readline()
                if line == b"\r\n":
                    break
                header_key, header_value = line.decode().split(":", 1)
                headers[header_key.strip()] = header_value.strip()

            self.logger.debug(f"Headers: {headers}")

            # Read body if Content-Length header is present
            body = None
            if 'Content-Length' in headers:
                content_length = int(headers['Content-Length'])
                body = await reader.read(content_length)
                self.logger.debug(f"Body: {body}")

            request = Request(first_line, headers, body)
            self.logger.info(f"Request path: {request.url}")

            response = await self._get_response(request)
            self.logger.debug(f"Response prepared.")
            writer.write(response.first_line)
            writer.write(response.headers)
            writer.write(response.body)
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")

            writer.write("HTTP/1.1 500 Internal Server Error\r\n")
            writer.write(" \r\n\n\n")
            writer.write(self.unhandled_request_response)
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

    async def _get_response(self, request: Request) -> Response:

        if request.method == 'GET':
            return self.gets[request.url](request)

        if request.method == 'POST':
            return self.posts[request.url](request)

        return Response(request.protocol, StatusCode.NOT_FOUND, {}, self.unhandled_request_response)
