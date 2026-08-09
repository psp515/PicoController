from microdot import Response

STATIC_DIR = "src/webui/static"


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

    @app.get("/style.css")
    async def style(request):
        return Response.send_file(STATIC_DIR + "/style.css")

    @app.get("/app.js")
    async def app_js(request):
        return Response.send_file(STATIC_DIR + "/app.js")
