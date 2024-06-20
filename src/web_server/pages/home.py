from web_server.request.request import Request


def get_home_page(request: Request):
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Controller Configuration</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: #222; /* Darker background */
            color: #f5f5f5;
            overflow: hidden; /* Prevent scrolling */
        }
        h1 {
            color: #f5f5f5;
        }
        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }
        .button {
            width: 200px;
            padding: 15px;
            font-size: 18px;
            color: #fff;
            background: linear-gradient(135deg, #0062cc, #004085); /* Gradient for buttons */
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            transition: background 0.3s, transform 0.3s; /* Smooth transition for hover effect */
        }
        .button:hover {
            background: linear-gradient(135deg, #004085, #002752); /* Darker gradient on hover */
            transform: scale(1.05); /* Slight zoom effect on hover */
        }
    </style>
</head>
<body>
    <h1>Controller Configuration</h1>
    <div class="container">
        <a href="/mqtt" class="button">MQTT Configuration</a>
        <a href="/wifi" class="button">WiFi Credentials</a>
        <a href="/strip" class="button">Strip Length</a>
    </div>
</body>
</html>

    """