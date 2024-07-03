import json

from configuration.options.strip_options import StripOptions
from devices.strip import Strip, MAX_PIXELS
from configuration_server.request.enums.status_code import StatusCode
from configuration_server.request.request import Request
from configuration_server.request.response import Response
from configuration_server.utils.html_builder import HtmlBuilder
from utils.logger import Logger


def get_strip_page(request: Request) -> Response:
    builder = HtmlBuilder()
    builder.set_title("Strip Configuration")
    builder.add_styles("configuration_server/styles/styles.css")
    builder.add_styles("configuration_server/styles/buttons.css")
    builder.add_styles("configuration_server/styles/inputs.css")

    builder.add_body("""
    <h1>Strip Configuration</h1>
    <div class="container">
        <label for="length" class="input-label">Number of neopixel leds</label>
        <input type="number" id="length" class="input-field" placeholder="Enter Strip Led Count" min="1" max="300">
        <button class="button" onclick="testLength()">Test Length</button>
        <button class="button" onclick="sendMqttCredentials()">Save</button>
        <button class="button back-button" onclick="goBack()">Back</button>
    </div>
    """)

    options = StripOptions()
    if not options.empty():
        value_script = "window.onload = function() {" + \
                       f"document.getElementById('length').value = '{options.length}';" + \
                       "};"
        builder.add_scripts(value_script)

    builder.add_scripts("""
    function testLength() {
        const length = document.getElementById('length').value;

        fetch('/strip/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ length}),
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to test strip.');
        });
    }""")
    builder.add_scripts("""
    function goBack() {
        fetch('/strip/reset', {
            method: 'POST',
            body: JSON.stringify({}),
        })
        window.location.href = '/';
    }""")
    builder.add_scripts("""
    function sendMqttCredentials() {
        const length = document.getElementById('length').value;

        fetch('/strip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ length}),
        })
        .then(response => {
            if (response.ok) {
                alert('Strip length saved successfully!');
            } else {
                alert('Failed to save strip length.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save strip length.');
        });
    }""")

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body=builder.build())


def post_strip_settings(request: Request) -> Response:
    content_type = request.headers.get('Content-Type', "")

    if content_type != 'application/json':
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options = StripOptions()
    json_body = json.loads(request.body)

    length = int(json_body.get('length', ""))

    if 0 > length > MAX_PIXELS:
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options.length = length

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")


def post_strip_test(request: Request) -> Response:
    content_type = request.headers.get('Content-Type', "")

    if content_type != 'application/json':
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    json_body = json.loads(request.body)

    length = int(json_body.get('length', ""))

    if length < 0:
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    logger = Logger()
    logger.debug("Testing strip length.")
    strip = Strip()

    strip.test_length(length)

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")


def post_reset(request: Request) -> Response:
    logger = Logger()
    logger.debug("Resetting strip length.")
    strip = Strip()
    strip.reset()

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")
