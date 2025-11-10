import os
import dash_vtk
from dash import html, dcc, Output, Input, no_update
from ..ids import *
from ..services.state import get_last_stl
from ..services.storage import OUTPUTS_URL_BASE

def layout():
    stl_path = get_last_stl()
    loading = not (stl_path and os.path.exists(stl_path))
    stl_url = f"{OUTPUTS_URL_BASE}/{os.path.basename(stl_path)}" if stl_path else ""
    return html.Main([
        html.Link(rel="stylesheet", href="/assets/style_viewer.css"),
        html.Header([
            html.Div("Converte AI", className="viewer-brand"),
            dcc.Link("Voltar", href="/", className="viewer-btn", id="link-voltar", refresh=False),
        ], className="viewer-topbar"),
        html.Section([
            html.H3("Visualização 3D do modelo gerado", style={"marginBottom": "18px"}),
            (html.Div([
                html.Div(className="futuristic-spinner"),
                html.Div("Convertendo imagem para modelo 3D...", style={"marginTop": "18px", "fontSize": "1.2rem", "color": "#7c4dff"})
            ], className="viewer-spinner viewer-3d"))
            if loading else dcc.Loading(
                id="loading-viewer",
                type="circle",
                children=[html.Div([
                    dash_vtk.View([
                        dash_vtk.GeometryRepresentation([dash_vtk.Reader(vtkClass="vtkSTLReader", url=stl_url)])
                    ], style={"height": "600px", "width": "100%"}),
                ], className="viewer-3d")],
                fullscreen=False,
            ),
            html.Div(f"Arquivo: {os.path.basename(stl_path) if stl_path else ''}", className="viewer-file"),
            html.Div([
                html.Button("Download STL", id=BTN_DOWNLOAD_VIEWER, className="viewer-btn", n_clicks=0),
                dcc.Download(id=DOWNLOAD_STL_VIEWER),
            ], className="viewer-download"),
        ], className="viewer-content"),
    ], className="viewer-frame")

def register_callbacks(app):
    @app.callback(
        Output(DOWNLOAD_STL_VIEWER, "data"),
        Input(BTN_DOWNLOAD_VIEWER, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_stl_viewer(n):
        stl_path = get_last_stl()
        if stl_path and os.path.exists(stl_path):
            return dcc.send_file(stl_path)
        return no_update
