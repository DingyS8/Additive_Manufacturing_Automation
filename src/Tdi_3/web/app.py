import os
from dash import Dash, html, dcc
from dash.dependencies import Output, Input, State
from flask import abort, send_from_directory
from .services.storage import OUT_DIR, OUTPUTS_URL_BASE
from .pages import loja, viewer, conta, admin

app = Dash(__name__, suppress_callback_exceptions=True, assets_folder=os.path.join(os.path.dirname(__file__), "..", "assets"))
server = app.server  # para gunicorn/uwsgi etc.

# rota para servir outputs (STL/OBJ/GCODE)
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

# container de páginas
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div(id="_pages")
])

# roteador simples
@app.callback(
    Output("_pages", "children"),
    Input("url", "pathname")       # ✅ classe de dependência
)
def display_page(pathname):
    if pathname == "/visualizar":
        return viewer.layout()
    elif pathname == "/conta":
        return conta.layout()
    elif pathname == "/admin":
        return admin.layout()
    else:
        return loja.layout()

# registrar callbacks das páginas
loja.register_callbacks(app)
viewer.register_callbacks(app)
