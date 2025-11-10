from dash import html, dcc

def render():
    return html.Div(
        id="customer-modal",
        className="customer-modal",
        style={"display": "none"},
        children=[
            html.Div(id="customer-modal-backdrop", className="customer-modal-backdrop", n_clicks=0),
            html.Div(
                className="customer-modal-card",
                children=[
                    html.Div(
                        [
                            html.Div("Cadastro do cliente", className="modal-title"),
                            html.Button("×", id="close-customer-modal", className="modal-close", n_clicks=0),
                        ],
                        className="customer-modal-header",
                    ),
                    html.Div(
                        className="customer-form-grid",
                        children=[
                            html.Div([html.Label("Nome completo", className="field-label"),
                                      dcc.Input(id="customer-name", type="text", placeholder="Seu nome", className="field-input", maxLength=120)], className="field-block"),
                            html.Div([html.Label("E-mail", className="field-label"),
                                      dcc.Input(id="customer-email", type="email", placeholder="voce@email.com", className="field-input", maxLength=120)], className="field-block"),
                            html.Div([html.Label("Telefone/WhatsApp", className="field-label"),
                                      dcc.Input(id="customer-phone", type="text", placeholder="(11) 99999-0000", className="field-input", maxLength=20)], className="field-block"),
                            html.Div([html.Label("CPF/CNPJ", className="field-label"),
                                      dcc.Input(id="customer-doc", type="text", placeholder="Somente números", className="field-input", maxLength=20)], className="field-block"),
                            html.Div([html.Label("Observações", className="field-label"),
                                      dcc.Textarea(id="customer-notes", placeholder="Preferências, endereço, etc.", className="field-textarea", maxLength=500)], className="field-block wide"),
                        ],
                    ),
                    html.Div(id="customer-feedback", className="customer-feedback"),
                    html.Div(
                        className="modal-actions",
                        children=[
                            html.Button("Cancelar", id="cancel-customer-modal", className="btn ghost", n_clicks=0),
                            html.Button("Salvar cadastro", id="btn-save-customer", className="btn", n_clicks=0),
                        ],
                    ),
                ],
            ),
        ],
    )
