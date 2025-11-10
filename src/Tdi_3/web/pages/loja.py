import io, os, base64, uuid
import dash_vtk
import trimesh
from PIL import Image
from dash import html, dcc, Input, Output, State, no_update, ctx
from ..ids import *
from ..components.customer_modal import render as customer_modal
from ..services.storage import out_path, OUTPUTS_URL_BASE
from ..services.state import set_last_stl
from ..services import triposr_adapter

APP_TITLE = "Converte AI"

def _parse_upload(contents):
    header, b64data = contents.split(",", 1)
    binary = base64.b64decode(b64data)
    return Image.open(io.BytesIO(binary)).convert("RGB")

def _obj_to_stl(obj_path, stl_path):
    mesh = trimesh.load(obj_path)
    mesh.export(stl_path)
    return stl_path

def layout():
    return html.Main(
        className="frame",
        children=[
            customer_modal(),
            html.Header(
                className="topbar",
                children=[
                    html.Div(APP_TITLE, id=BRAND, className="brand"),
                    html.Button(html.Div(className="hex"), id=BTN_PROFILE, className="hex-btn", title="Cadastro do cliente"),
                ],
            ),
            html.Section(
                className="content",
                children=[
                    dcc.Upload(
                        id=UPLOADER, accept="image/*", multiple=False, disabled=False,
                        className="dropzone",
                        children=html.Div(className="drop-inner", children=[
                            html.Div(className="upld", children=html.Span("⤴", className="upld-ico")),
                            html.Div("Solte a imagem aqui", className="drop-title"),
                            html.Div("ou clique para selecionar um arquivo", className="hint"),
                        ]),
                    ),
                    html.Div(id=PREVIEW, className="preview",
                             children=[html.Div(className="thumb", children=[
                                 html.Img(id=PREVIEW_IMG, src="", className="thumb-img", alt="preview"),
                                 html.Button("×", id=REMOVE_IMG, className="thumb-x", title="Remover imagem"),
                             ])],
                             style={"display": "none"}),
                    html.Div(className="preproc-opts", children=[
                        html.Label("Remover fundo?"),
                        dcc.Checklist(id=DO_REMOVE_BG, options=[{"label":"Sim", "value":"yes"}], value=["yes"], inline=True),
                        html.Label("Foreground ratio (0.5 a 1.0):"),
                        dcc.Slider(id=FG_RATIO, min=0.5, max=1.0, step=0.05, value=0.85,
                                   marks={0.5:"0.5", 0.7:"0.7", 0.85:"0.85", 1.0:"1.0"}),
                    ]),
                    html.Div(className="divider", children=[html.Div(className="line"), html.Span("Ou"), html.Div(className="line")]),
                    html.Div("Insira sua descrição", className="label"),
                    dcc.Textarea(id=DESCRICAO, className="textarea", placeholder="Digite até 5000 caracteres...",
                                 maxLength=5000, disabled=False, value=""),
                    html.Div(className="meta", children=[
                        html.Span("Nenhum arquivo selecionado", id=FILE_META),
                        html.Span([html.Span("0", id=COUNT), "/5000"]),
                    ]),
                    html.Div(className="actions", children=[
                        dcc.Loading(id="loading-converter", type="default",
                                    children=html.Div(id=CONVERSION_SPINNER_TARGET, children=[
                                        html.Button("Converter", id=BTN_CONVERTER, className="btn"),
                                        dcc.Download(id=DOWNLOAD_STL),
                                    ])),
                        html.Button("Limpar", id=BTN_LIMPAR, className="btn ghost"),
                    ]),
                    html.Div(id=MAIN_LOADING),
                    dcc.Store(id=STORE_IMG, data=""),
                    dcc.Store(id=STORE_CUSTOMER, data={}),
                ],
            ),
        ],
    )

def register_callbacks(app):

    # spinner principal
    @app.callback(Output(MAIN_LOADING, "children"),
                  Input(BTN_CONVERTER, "n_clicks"),
                  prevent_initial_call=True)
    def show_main_loading(n):
        if n:
            return html.Div([
                html.Div(className="futuristic-spinner"),
                html.Div("Convertendo imagem para modelo 3D...", style={"marginTop": "12px", "fontSize": "1.1rem", "color": "#7c4dff"})
            ], className="main-spinner")
        return ""

    # modal
    @app.callback(
        Output("customer-modal", "style"),
        Input(BTN_PROFILE, "n_clicks"),
        Input("close-customer-modal", "n_clicks"),
        Input("cancel-customer-modal", "n_clicks"),
        Input("customer-modal-backdrop", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_customer_modal(open_clicks, close_clicks, cancel_clicks, backdrop_clicks):
        trigger = ctx.triggered_id
        if trigger == BTN_PROFILE:
            return {"display": "flex"}
        return {"display": "none"}

    # salvar cadastro (mesmo código que você já tinha — mantido)
    @app.callback(
        Output("customer-feedback", "children"),
        Output(STORE_CUSTOMER, "data"),
        Input("btn-save-customer", "n_clicks"),
        State("customer-name", "value"),
        State("customer-email", "value"),
        State("customer-phone", "value"),
        State("customer-doc", "value"),
        State("customer-notes", "value"),
        prevent_initial_call=True,
    )
    def save_customer_data(n, name, email, phone, doc, notes):
        if not n:
            return no_update, no_update
        errors = []
        name = (name or "").strip()
        email = (email or "").strip()
        phone_raw = "".join(filter(str.isdigit, (phone or "")))
        doc_raw = "".join(filter(str.isdigit, (doc or "")))
        notes = (notes or "").strip()

        if len(name) < 3:
            errors.append("Informe um nome válido.")
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Informe um e-mail válido.")
        if phone_raw and len(phone_raw) < 10:
            errors.append("Telefone incompleto. Use DDD + número.")
        if doc_raw and len(doc_raw) not in (0, 11, 14):
            errors.append("CPF/CNPJ deve conter 11 ou 14 dígitos.")

        if errors:
            return html.Div([html.P(msg) for msg in errors], className="alert alert-error"), no_update

        data = {"name": name, "email": email, "phone": phone_raw, "document": doc_raw, "notes": notes}
        return html.Div("Cadastro salvo com sucesso. Você já pode avançar para o carrinho e pagamentos.", className="alert alert-success"), data

    # estado da UI (mesmo core que você já tinha)
    @app.callback(
        Output(STORE_IMG, "data"),
        Output(UPLOADER, "contents"),
        Output(UPLOADER, "disabled"),
        Output(DESCRICAO, "value"),
        Output(DESCRICAO, "disabled"),
        Output(FILE_META, "children"),
        Output(PREVIEW, "style"),
        Output(PREVIEW_IMG, "src"),
        Output(COUNT, "children"),
        Input(UPLOADER, "contents"),
        Input(DESCRICAO, "value"),
        Input(REMOVE_IMG, "n_clicks"),
        Input(BTN_LIMPAR, "n_clicks"),
        State(STORE_IMG, "data"),
        prevent_initial_call=False,
    )
    def ui_state(upl_contents, texto, remove_clicks, clear_clicks, img_store):
        trigger = ctx.triggered_id
        texto = (texto or "")

        store = img_store or ""
        uploader_contents = no_update
        uploader_disabled = False
        desc_val = texto
        desc_disabled = False
        file_meta = "Nenhum arquivo selecionado"
        preview_style = {"display": "none"}
        preview_src = ""
        count = len(texto)

        if store:
            preview_style = {"display": "block"}
            preview_src = store
            desc_disabled = True
            desc_val = ""
            file_meta = "1 arquivo selecionado"

        if trigger == BTN_LIMPAR:
            return "", None, False, "", False, "Nenhum arquivo selecionado", {"display":"none"}, "", 0

        if trigger == REMOVE_IMG:
            return "", None, False, desc_val, False, "Nenhum arquivo selecionado", {"display":"none"}, "", len(desc_val)

        if trigger == UPLOADER and upl_contents:
            size_kb = int(len(upl_contents) * 3 / 4 / 1024)
            file_meta = f"1 arquivo • ~{size_kb} KB"
            return upl_contents, upl_contents, False, "", True, file_meta, {"display":"block"}, upl_contents, 0

        if len(texto) > 0 and not store:
            uploader_disabled = True
            file_meta = "Nenhum arquivo selecionado"
            return "", None, uploader_disabled, texto, False, file_meta, {"display":"none"}, "", len(texto)

        return store, uploader_contents, desc_disabled, desc_val, desc_disabled, file_meta, preview_style, preview_src, count

    # conversão (navega usando dcc.Location mudando pathname)
    @app.callback(
        Output(URL, "pathname"),
        Output(CONVERSION_SPINNER_TARGET, "children"),
        Input(BTN_CONVERTER, "n_clicks"),
        State(STORE_IMG, "data"),
        State(DESCRICAO, "value"),
        State(DO_REMOVE_BG, "value"),
        State(FG_RATIO, "value"),
        prevent_initial_call=True,
    )
    def run_convert(n, b64img, texto, do_remove_bg_val, fg_ratio):
        texto = (texto or "").strip()
        if not b64img and not texto:
            return no_update, no_update

        name = f"{uuid.uuid4().hex[:8]}"
        obj_path = out_path(name, "obj")
        stl_path = out_path(name, "stl")
        do_remove_bg = bool(do_remove_bg_val and "yes" in do_remove_bg_val)
        fg_ratio = fg_ratio if fg_ratio is not None else 0.85

        if b64img:
            pil = _parse_upload(b64img)
            triposr_adapter.image_to_obj(pil, obj_path, remove_bg=do_remove_bg, fg_ratio=fg_ratio)
            _obj_to_stl(obj_path, stl_path)
        else:
            # MOCK texto -> STL (mantido)
            r = min(2.0, 0.5 + len(texto.strip()) / 1000.0)
            mesh = trimesh.creation.icosphere(radius=r, subdivisions=3)
            mesh.export(stl_path)

        set_last_stl(stl_path)
        return "/visualizar", ""
