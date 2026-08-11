from microdot import Response

STATIC_DIR = "src/webui/static"

ICONS = {
    "logo.svg",
    "menu.svg",
    "wifi.svg",
    "flash.svg",
    "upload.svg",
    "restart.svg",
    "save.svg",
}


def register_ui_routes(app):
    @app.get("/")
    async def index(request):
        return Response.send_file(STATIC_DIR + "/index.html")

    @app.get("/modes")
    async def modes_page(request):
        return Response.send_file(STATIC_DIR + "/modes.html")

    @app.get("/config")
    async def config_page(request):
        return Response.send_file(STATIC_DIR + "/config.html")

    @app.get("/styles/style.css")
    async def style(request):
        return Response.send_file(STATIC_DIR + "/styles/style.css")

    @app.get("/js/app.js")
    async def app_js(request):
        return Response.send_file(STATIC_DIR + "/js/app.js")

    @app.get("/icons/<string:name>")
    async def icon(request, name):
        if name not in ICONS:
            return {"error": "not found"}, 404
        return Response.send_file(STATIC_DIR + "/icons/" + name)
