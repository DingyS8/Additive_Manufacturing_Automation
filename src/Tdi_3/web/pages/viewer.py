import os
from dash import html, dcc
import dash_vtk
from dash.dependencies import Output, Input
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
            html.Div([
                html.Button("Download STL", id="btn-download-viewer", className="viewer-btn"),
                dcc.Download(id="download-stl-viewer"),
                html.Button("Confirmar modelo e fatiar", id="btn-confirm-viewer", className="viewer-btn"),
            ], className="viewer-download"),
            html.Div(id="orcamento-viewer", className="viewer-orcamento"),
        ], className="viewer-content")
    ], className="viewer-frame")

def register_callbacks(app):
    from ..services.slicer import slice_model
    from ..services.quote import estimate_from_gcode

    @app.callback(Output("download-stl-viewer","data"),
                  Input("btn-download-viewer","n_clicks"), prevent_initial_call=True)
    def download(n):
        if _LAST_STL["path"]:
            return dcc.send_file(_LAST_STL["path"])

    @app.callback(Output("orcamento-viewer","children"),
                  Input("btn-confirm-viewer","n_clicks"), prevent_initial_call=True)
    def confirmar_e_fatiar(n):
        if not _LAST_STL["path"]:
            return "Nenhum modelo STL carregado."
        try:
            gcode_path = slice_model(_LAST_STL["path"])
            orcamento = estimate_from_gcode(gcode_path)
            return html.Div([
                html.H4("Orçamento para impressão:"),
                html.Ul([
                    html.Li(f"Tempo estimado: {orcamento['time_h']} horas"),
                    html.Li(f"Filamento: {orcamento['filament_m']} metros"),
                    html.Li(f"Energia: {orcamento['energy_kwh']} kWh"),
                    html.Li(f"Total: R$ {orcamento['total']}")
                ]),
                html.Div("Confirme o pagamento para prosseguir com a impressão.", className="orcamento-hint")
            ])
        except Exception as e:
            return f"Erro ao fatiar STL: {e}"
