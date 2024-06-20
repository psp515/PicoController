from web_server.request.enums.httpmethod import HttpMethod
from web_server.request.exceptions.invalid_http_data import InvalidHttpData


class Request:
    def __init__(self, raw):
        self._method = ""
        self._url = ""
        self._query_string = ""

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        self._parse_request(raw)

    def _parse_request(self, raw):
        if len(raw) == 0:
            raise InvalidHttpData("Empty request")

        eol_char = '\r\n'
        if raw.find('\r\n') == -1:
            eol_char = '\n'

        lines = raw.split(eol_char)

        self._parse_basic_information(lines[0])

        if len(lines) == 1:
            return

        # Logic not handled

    def _parse_basic_information(self, first_line):
        parts = first_line.split()

        if len(parts) != 3:
            raise InvalidHttpData("First line of request is not valid HTTP request line")

        self._method = parts[0]

        url_parts = parts[1].split('?', 1)
        self._url = url_parts[0]

        if len(url_parts) > 1:
            self._query_string = url_parts[1]

        # Skip protocol
        # self.protocol = parts[2]

    @property
    def method(self):
        if self._method.upper() == HttpMethod.GET:
            return HttpMethod.GET
        elif self._method.upper() == HttpMethod.POST:
            return HttpMethod.POST

        raise InvalidHttpData(f"Request method not handled {self._method}")

    @property
    def url(self):
        return self._url

    @property
    def query_string(self):
        return self._query_string
