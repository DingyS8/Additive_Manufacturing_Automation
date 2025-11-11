import os
from dash import Dash, html, dcc
from dash.dependencies import Output, Input
from flask import abort, send_from_directory
from .services.storage import OUT_DIR, OUTPUTS_URL_BASE
from .services.db import ensure_indexes
from .pages import loja, viewer, conta, admin

ensure_indexes()  # cria índices no startup

app = Dash(__name__, suppress_callback_exceptions=True, assets_folder=os.path.join(os.path.dirname(__file__), "assets"))
server = app.server

@server.route(f"{OUTPUTS_URL_BASE}/<path:filename>")
def serve_generated_outputs(filename):
    safe_path = os.path.abspath(os.path.join(OUT_DIR, filename))
    try:
        if os.path.commonpath([safe_path, OUT_DIR]) != OUT_DIR:
            abort(404)
    except ValueError:
        abort(404)
    if not os.path.exists(safe_path):
        abort(404)
    relative_name = os.path.relpath(safe_path, OUT_DIR)
    return send_from_directory(OUT_DIR, relative_name)

app.layout = html.Div([ dcc.Location(id="url"), html.Div(id="_pages") ])

@app.callback(Output("_pages","children"), Input("url","pathname"))
def display_page(pathname):
    if pathname == "/visualizar": return viewer.layout()
    if pathname == "/conta":      return conta.layout()
    if pathname == "/admin":      return admin.layout()
    return loja.layout()

loja.register_callbacks(app)
viewer.register_callbacks(app)
conta.register_callbacks(app)
admin.register_callbacks(app)
