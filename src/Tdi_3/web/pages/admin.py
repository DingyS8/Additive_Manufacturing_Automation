from dash import html, dcc, Input, Output, State, no_update
from ..services.orders import list_all_orders, update_status
from ..services.printer import set_printer_params, upload_gcode, start_print

def layout():
    orders = list_all_orders()
    return html.Main(className="frame", children=[
        html.Header(className="topbar", children=[
            dcc.Link("← Loja", href="/", className="btn ghost"),
            html.Div("Admin", className="brand")
        ]),
        html.Section(className="content", children=[
            html.H3("Pedidos"),
            html.Ul([ html.Li(f"id:{o['_id']} — {o['status']} — total:{o['total']} — itens:{len(o['items'])}") for o in orders ]),
            html.Div(className="actions", children=[
                dcc.Input(id="admin-oid", type="text", placeholder="id do pedido"),
                dcc.Dropdown(id="admin-status", options=[
                    {"label": s, "value": s} for s in ["PENDENTE_PAGAMENTO","PAGO","IMPRIMINDO","FINALIZADO","ENVIADO","ENTREGUE","CANCELADO"]
                ], placeholder="novo status"),
                html.Button("Atualizar status", id="btn-admin-status", className="btn"),
            ]),
            html.Hr(),
            html.H3("Impressora"),
            html.Div(className="actions", children=[
                dcc.Input(id="p-bed", type="number", placeholder="bed °C"),
                dcc.Input(id="p-nozzle", type="number", placeholder="nozzle °C"),
                html.Button("Ajustar", id="btn-prn-params", className="btn ghost"),
            ]),
            html.Div(className="actions", children=[
                dcc.Input(id="p-file", type="text", placeholder="caminho do .gcode"),
                html.Button("Enviar", id="btn-prn-upload", className="btn"),
                dcc.Input(id="p-name", type="text", placeholder="nome do gcode no host"),
                html.Button("Iniciar", id="btn-prn-start", className="btn"),
            ]),
            html.Div(id="admin-feedback", className="customer-feedback"),
        ])
    ])

def register_callbacks(app):
    @app.callback(Output("admin-feedback","children"),
                  Input("btn-admin-status","n_clicks"),
                  State("admin-oid","value"), State("admin-status","value"),
                  prevent_initial_call=True)
    def change_status(n, oid, status):
        if not oid or not status: return "Preencha id e status."
        update_status(oid, status)
        return "Status atualizado."

    @app.callback(Output("admin-feedback","children"),
                  Input("btn-prn-params","n_clicks"),
                  State("p-bed","value"), State("p-nozzle","value"),
                  prevent_initial_call=True)
    def params(n, bed, nozzle):
        res = set_printer_params(bed, nozzle)
        return f"Parâmetros enviados: {res}"

    @app.callback(Output("admin-feedback","children"),
                  Input("btn-prn-upload","n_clicks"),
                  State("p-file","value"),
                  prevent_initial_call=True)
    def up(n, path):
        if not path: return "Informe caminho."
        res = upload_gcode("default", path)
        return f"Upload: {res}"

    @app.callback(Output("admin-feedback","children"),
                  Input("btn-prn-start","n_clicks"),
                  State("p-name","value"),
                  prevent_initial_call=True)
    def start(n, name):
        if not name: return "Informe nome."
        res = start_print("default", name)
        return f"Start: {res}"
