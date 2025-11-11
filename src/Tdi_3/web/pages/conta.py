from dash import html, dcc, Input, Output, State, no_update, ctx
from ..services.cart import get_cart, remove_item, clear_cart
from ..services.orders import create_order, list_orders_by_user, cancel_order
from ..services.payments import create_boleto_mock, confirm_payment_mock
from ..services.invoice import issue_nfe_mock

def layout():
    user_id = "demo-user"
    cart = get_cart(user_id)
    orders = list_orders_by_user(user_id)
    return html.Main(className="frame", children=[
        html.Header(className="topbar", children=[
            dcc.Link("← Loja", href="/", className="btn ghost"),
            html.Div("Minha Conta", className="brand")
        ]),
        html.Section(className="content", children=[
            html.H3("Carrinho"),
            html.Ul([ html.Li(f"{it['type']} — {it.get('quote',{}).get('total','-')} R$  — id:{it['id']}") for it in cart["items"] ]),
            html.Div(className="actions", children=[
                html.Button("Criar pedido", id="btn-create-order", className="btn"),
                html.Button("Limpar carrinho", id="btn-clear-cart", className="btn ghost"),
            ]),
            html.Hr(),
            html.H3("Meus pedidos"),
            html.Div(id="orders-area", children=[
                html.Ul([ html.Li(f"Status: {o['status']} — Total: {o['total']} R$ — id:{o['_id']}") for o in orders ])
            ]),
            html.Div(className="actions", children=[
                dcc.Input(id="order-id", type="text", placeholder="id do pedido"),
                html.Button("Cancelar pedido", id="btn-cancel-order", className="btn ghost"),
                html.Button("Gerar boleto (mock)", id="btn-boleto", className="btn"),
                html.Button("Confirmar pagamento (mock)", id="btn-confirm", className="btn"),
                html.Button("Emitir NFe (mock)", id="btn-nfe", className="btn"),
            ]),
            html.Div(id="conta-feedback", className="customer-feedback"),
        ])
    ])

def register_callbacks(app):
    @app.callback(Output("conta-feedback","children"),
                  Input("btn-clear-cart","n_clicks"),
                  prevent_initial_call=True)
    def clear(n):
        user_id="demo-user"
        clear_cart(user_id)
        return "Carrinho limpo."

    @app.callback(Output("conta-feedback","children"),
                  Input("btn-create-order","n_clicks"),
                  prevent_initial_call=True)
    def create(n):
        user_id="demo-user"
        cart = get_cart(user_id)
        total = 0.0
        for it in cart["items"]:
            if "quote" in it: total += it["quote"]["total"]
        order = create_order(user_id, cart["items"], round(total,2))
        clear_cart(user_id)
        return f"Pedido criado: {order.get('_id','(sem id)')} total {order['total']}"

    @app.callback(Output("conta-feedback","children"),
                  Input("btn-cancel-order","n_clicks"),
                  State("order-id","value"), prevent_initial_call=True)
    def cancel(n, oid):
        if not oid: return "Informe o id."
        cancel_order(oid, user_id="demo-user", is_admin=False)
        return "Pedido cancelado (se permitido)."

    @app.callback(Output("conta-feedback","children"),
                  Input("btn-boleto","n_clicks"),
                  State("order-id","value"), prevent_initial_call=True)
    def boleto(n, oid):
        if not oid: return "Informe o id."
        p = create_boleto_mock(oid)
        return f"Boleto gerado (mock): {p['linha_digitavel']}"

    @app.callback(Output("conta-feedback","children"),
                  Input("btn-confirm","n_clicks"),
                  State("order-id","value"), prevent_initial_call=True)
    def confirm(n, oid):
        if not oid: return "Informe o id."
        confirm_payment_mock(oid)
        return "Pagamento confirmado (mock)."

    @app.callback(Output("conta-feedback","children"),
                  Input("btn-nfe","n_clicks"),
                  State("order-id","value"), prevent_initial_call=True)
    def nfe(n, oid):
        if not oid: return "Informe o id."
        inv = issue_nfe_mock(oid)
        return f"NFe emitida (mock): {inv['nfe_number']}"
