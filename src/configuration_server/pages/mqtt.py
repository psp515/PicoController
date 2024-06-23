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
        <input type="number" id="port" class="input-field" placeholder="Enter Port" min="1" max="65535">
        <input type="text" id="username" class="input-field" placeholder="Enter Username">
        <input type="password" id="password" class="input-field" placeholder="Enter Password">
        <input type="text" id="client" class="input-field" placeholder="Enter Client Id">
        <input type="number" id="keep_alive" class="input-field" placeholder="Enter Keep Alive" min="30" max="300">
        
        <input type="text" id="topic" class="input-field" placeholder="Enter Device Topic">
        
        <button class="button" onclick="sendMqttSettings()">Save</button>
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
                       f"document.getElementById('client').value = '{options.client}';" + \
                       f"document.getElementById('keep_alive').value = '{options.keep_alive}';" + \
                       f"document.getElementById('topic').value = '{options.topic}';" + \
                       "};"
        builder.add_scripts(value_script)

    builder.add_scripts("""
    function goBack() {
        window.location.href = '/';
    }""")
    builder.add_scripts("""
    function sendMqttSettings() {
        const url = document.getElementById('url').value;
        const port = document.getElementById('port').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const client = document.getElementById('client').value;
        const keep_alive = document.getElementById('keep_alive').value;
        const topic = document.getElementById('topic').value;

        fetch('/mqtt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, port, username, password, topic, keep_alive, client }),
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


def post_mqtt_settings(request: Request) -> Response:
    content_type = request.headers.get('Content-Type', "")

    if content_type != 'application/json':
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options = MqttOptions()
    json_body = json.loads(request.body)

    url = json_body.get('url', "")
    port = int(json_body.get('port', 0))
    username = json_body.get('username', "")
    password = json_body.get('password', "")
    client = json_body.get('client', "")
    keep_alive = int(json_body.get('keep_alive', 0))
    topic = json_body.get('topic', "")

    if url == "" \
            or username == "" \
            or password == "" \
            or client == ""\
            or topic == "" \
            or port <= 0 or port >= 65536 \
            or keep_alive < 30 or keep_alive > 300:
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options.url = url.strip()
    options.port = port
    options.username = username.strip()
    options.password = password.strip()
    options.client = client.strip()
    options.keep_alive = keep_alive
    options.topic = topic.strip()

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")
