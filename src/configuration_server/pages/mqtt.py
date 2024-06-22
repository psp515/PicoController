import json

from configuration.features.mqtt_options import MqttOptions
from configuration_server.request.enums.status_code import StatusCode
from configuration_server.request.request import Request
from configuration_server.request.response import Response
from configuration_server.utils.html_builder import HtmlBuilder


def get_mqtt_page(request: Request) -> Response:
    builder = HtmlBuilder()
    builder.set_title("MQTT Configuration")
    builder.add_styles("configuration_server/styles/styles.css")
    builder.add_styles("configuration_server/styles/buttons.css")
    builder.add_styles("configuration_server/styles/inputs.css")

    builder.add_body("""
    <h1>MQTT Configuration</h1>
    <div class="container">
        <input type="text" id="url" class="input-field" placeholder="Enter URL">
        <input type="number" id="port" class="input-field" placeholder="Enter Port">
        <input type="text" id="username" class="input-field" placeholder="Enter Username">
        <input type="password" id="password" class="input-field" placeholder="Enter Password">
        <button class="button" onclick="sendMqttCredentials()">Save</button>
        <button class="button back-button" onclick="goBack()">Back</button>
    </div>
    """)

    options = MqttOptions()
    if not options.empty():
        value_script = "window.onload = function() {" + \
                       f"document.getElementById('url').value = '{options.url}';" + \
                       f"document.getElementById('port').value = '{options.port}';" + \
                       f"document.getElementById('username').value = '{options.username}';" + \
                       f"document.getElementById('password').value = '{options.password}';" + \
                       "};"
        builder.add_scripts(value_script)

    builder.add_scripts("""
    function goBack() {
        window.location.href = '/';
    }""")
    builder.add_scripts("""
    function sendMqttCredentials() {
        const url = document.getElementById('url').value;
        const port = document.getElementById('port').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        fetch('/mqtt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, port, username, password }),
        })
        .then(response => {
            if (response.ok) {
                alert('MQTT credentials saved successfully!');
            } else {
                alert('Failed to save MQTT credentials.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save MQTT credentials.');
        });
    }""")

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body=builder.build())


def post_mqtt_credentials(request: Request) -> Response:
    content_type = request.headers.get('Content-Type', "")

    if content_type != 'application/json':
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options = MqttOptions()
    json_body = json.loads(request.body)

    url = json_body.get('url', "")
    port = json_body.get('port', "")
    username = json_body.get('username', "")
    password = json_body.get('password', "")

    if url == "" or port == "" or username == "" or password == "":
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options.url = url
    options.port = port
    options.username = username
    options.password = password

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")
