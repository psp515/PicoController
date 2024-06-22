from web_server.request.enums.http_method import HttpMethod
from web_server.request.exceptions.invalid_http_data import InvalidHttpData


class Request:
    def __init__(self, first_line: bytes, headers: {}, body: bytes = None):
        self._protocol = ""
        self._method = ""
        self._url = ""
        self._query_string = ""
        self._headers = headers
        self._body = body.decode('utf-8') if body else ""
        first_line = first_line.decode('utf-8') if first_line else ""
        self._parse_first_line(first_line)

    def _parse_first_line(self, first_line):
        if len(first_line) == 0:
            raise InvalidHttpData("Empty request")

        eol_char = '\r\n'
        if first_line.find('\r\n') == -1:
            eol_char = '\n'

        lines = first_line.split(eol_char)

        self._parse_basic_information(lines[0])

    def _parse_basic_information(self, first_line):
        parts = first_line.split()

        if len(parts) != 3:
            raise InvalidHttpData("First line of request is not valid HTTP request line")

        self._method = parts[0]

        url_parts = parts[1].split('?', 1)
        self._url = url_parts[0]

        if len(url_parts) > 1:
            self._query_string = url_parts[1]

        self._protocol = parts[2]

    @property
    def method(self) -> HttpMethod:
        if self._method.upper() == HttpMethod.GET:
            return HttpMethod.GET
        elif self._method.upper() == HttpMethod.POST:
            return HttpMethod.POST

        raise InvalidHttpData(f"Request method not handled {self._method}")

    @property
    def headers(self) -> {}:
        return self._headers

    @property
    def body(self) -> str:
        return self._body

    @property
    def url(self) -> str:
        return self._url

    @property
    def query_string(self) -> str:
        return self._query_string

    @property
    def protocol(self) -> str:
        return self._protocol
