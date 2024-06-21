

class Response:
    def __init__(self, protocol: str,
                 status_code: str,
                 headers: dict,
                 body: str):
        self._first_line = f"{protocol} {status_code}"
        self._headers = headers
        self._body = body

    def __str__(self):
        return f"{self.first_line}\r\n{self.headers}\r\n\r\n{self.body}".encode('utf-8')

    @property
    def headers(self):
        headers = '\n'.join(f'{key}: {value}' for key, value in self._headers.items())
        return f"{headers}\r\n\r\n"

    @property
    def body(self):
        return self._body

    @property
    def first_line(self):
        return f"{self._first_line}\r\n"
