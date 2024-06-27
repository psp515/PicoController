import asyncio
from machine import reset

from utils.logger import Logger
from configuration_server.request.enums.status_code import StatusCode
from configuration_server.request.request import Request
from configuration_server.request.response import Response
from configuration_server.utils.html_builder import HtmlBuilder


def get_home_page(request: Request) -> Response:
    builder = HtmlBuilder()
    builder.set_title("Controller Configuration")
    builder.add_styles("configuration_server/styles/styles.css")
    builder.add_styles("configuration_server/styles/buttons.css")

    builder.add_body("""    
    <h1>Controller Configuration</h1>
    <div class="container">
        <button class="button" onclick="gotToMqttPage()">Mqtt Configuration</button>
        <button class="button" onclick="gotToWiFiPage()">WiFi Credentials</button>
        <button class="button" onclick="gotToStripPage()">Strip Length</button>
        <button class="button back-button" onclick="restart()">Restart</button>
    </div>""")

    builder.add_scripts("""
    function restart() {
        fetch('/restart', {
            method: 'POST',
            body: JSON.stringify({}),
        })
        .then(response => {
            if (response.ok) {
                alert('Restarting...');
            } else {
                alert('Failed to restart.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to restart.');
        });
    } """)
    builder.add_scripts("""
    function gotToMqttPage() {
        window.location.href = '/mqtt';
    } """)
    builder.add_scripts("""
    function gotToWiFiPage() {
        window.location.href = '/wifi';
    } """)
    builder.add_scripts("""
    function gotToStripPage() {
        window.location.href = '/strip';
    } """)

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body=builder.build())


async def _restart():
    await asyncio.sleep(2)
    reset()


def restart_device(request: Request) -> Response:
    logger = Logger()
    logger.info("Restarting device.")
    asyncio.create_task(_restart())
    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")
