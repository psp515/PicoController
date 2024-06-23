import json

from configuration.features.wifi_options import WifiOptions
from configuration_server.request.enums.status_code import StatusCode
from configuration_server.request.request import Request
from configuration_server.request.response import Response
from configuration_server.utils.html_builder import HtmlBuilder


def get_wifi_page(request: Request) -> Response:
    builder = HtmlBuilder()
    builder.set_title("WiFi Configuration")
    builder.add_styles("configuration_server/styles/styles.css")
    builder.add_styles("configuration_server/styles/buttons.css")
    builder.add_styles("configuration_server/styles/inputs.css")

    builder.add_body("""
    <h1>WiFi Configuration</h1>
    <div class="container">
        <label for="ssid" class="input-label">SSID (WiFi Network Name)</label>
        <input type="text" id="ssid" class="input-field" placeholder="Enter SSID">
        <label for="password" class="input-label">Password</label>
        <input type="password" id="password" class="input-field" placeholder="Enter Password">
        <button class="button" onclick="sendWifiCredentials()">Save</button>
        <button class="button back-button" onclick="goBack()">Back</a>
    </div>
    """)

    options = WifiOptions()
    if not options.empty():

        value_script = "window.onload = function() {" + \
                       f"document.getElementById('ssid').value = '{options.ssid}';" + \
                       f"document.getElementById('password').value = '{options.password}';" + \
                       "};"

        builder.add_scripts(value_script)

    builder.add_scripts("""
    function goBack() {
        window.location.href = '/';
    }""")
    builder.add_scripts("""
    function sendWifiCredentials() {
            const ssid = document.getElementById('ssid').value;
            const password = document.getElementById('password').value;

            fetch('/wifi', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ssid, password }),
            })
            .then(response => {
                if (response.ok) {
                    alert('WiFi credentials saved successfully!');
                } else {
                    alert('Failed to save WiFi credentials.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to save WiFi credentials.');
            });
        }
    """)

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body=builder.build())


def post_credentials(request: Request) -> Response:
    content_type = request.headers.get('Content-Type', "")

    if content_type != 'application/json':
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options = WifiOptions()
    json_body = json.loads(request.body)

    ssid = json_body.get('ssid', "")
    password = json_body.get('password', "")

    if ssid == "" or password == "" or len(ssid) > 32 or len(password) > 64:
        return Response(protocol=request.protocol, status_code=StatusCode.BAD_REQUEST, headers={}, body="")

    options.ssid = ssid.strip()
    options.password = password.strip()

    return Response(protocol=request.protocol, status_code=StatusCode.OK, headers={}, body="")
