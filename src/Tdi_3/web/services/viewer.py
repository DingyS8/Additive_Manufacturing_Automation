import os
from dash import html, dcc
import dash_vtk
from ..services.storage import OUTPUTS_URL_BASE

# Você pode trocar isso por store/estado global
_LAST_STL = {"path": None}

def set_last_stl(path): _LAST_STL["path"] = path

def layout():
    stl_path = _LAST_STL["path"]
    stl_url = f"{OUTPUTS_URL_BASE}/{os.path.basename(stl_path)}" if stl_path else None
    return html.Main([
        html.Link(rel="stylesheet", href="/assets/style_viewer.css"),
        html.Header([html.Div("Converte AI", className="viewer-brand"),
                     dcc.Link("Voltar", href="/", className="viewer-btn")], className="viewer-topbar"),
        html.Section([
            html.H3("Visualização 3D"),
            (dcc.Loading(children=[
                html.Div([dash_vtk.View([
                    dash_vtk.GeometryRepresentation([ dash_vtk.Reader(vtkClass="vtkSTLReader", url=stl_url) ])
                ], style={"height":"600px","width":"100%"})], className="viewer-3d")
            ]) if stl_url else html.Div("Sem STL", className="viewer-3d")),
            html.Div([ html.Button("Download STL", id="btn-download-viewer", className="viewer-btn"),
                       dcc.Download(id="download-stl-viewer") ], className="viewer-download"),
        ], className="viewer-content")
    ], className="viewer-frame")

def register_callbacks(app):
    @app.callback(dcc.Output("download-stl-viewer","data"),
                  dcc.Input("btn-download-viewer","n_clicks"), prevent_initial_call=True)
    def download(n):
        if _LAST_STL["path"]:
            return dcc.send_file(_LAST_STL["path"])
