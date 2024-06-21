from web_server.request.enums.status_code import StatusCode
from web_server.request.request import Request
from web_server.request.response import Response
from web_server.utils.html_builder import HtmlBuilder


def get_home_page(request: Request) -> Response:
    builder = HtmlBuilder()
    builder.set_title("Controller Configuration")
    builder.add_styles("web_server/styles/styles.css")
    builder.add_styles("web_server/styles/buttons.css")

    builder.add_body("""    
    <h1>Controller Configuration</h1>
    <div class="container">
        <a href="/mqtt" class="button">MQTT Configuration</a>
        <a href="/wifi" class="button">WiFi Credentials</a>
        <a href="/strip" class="button">Strip Length</a>
    </div>""")

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body=builder.build())
