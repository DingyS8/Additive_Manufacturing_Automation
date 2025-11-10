from dash import html

def layout():
    return html.Main(className="frame", children=[
        html.Header(className="topbar", children=[html.Div("Em breve", className="brand")]),
        html.Section(className="content", children=[html.P("Tela em construção.")])
    ])

def register_callbacks(app): 
    pass
