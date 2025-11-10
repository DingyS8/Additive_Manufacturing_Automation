import os, io, base64, uuid
import os
import dash_vtk
from PIL import Image
import trimesh
from flask import abort, send_from_directory
# --- TripoSR integration ---
import sys
TRIPOSR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), r'C:\Users\vinic\Desktop\GitHub\TripoSR'))
if TRIPOSR_PATH not in sys.path:
    sys.path.insert(0, TRIPOSR_PATH)
try:
    from gradio_app import preprocess, generate
except ImportError:
    preprocess = None
    generate = None

from dash import Dash, html, dcc, Input, Output, State, no_update, ctx

APP_TITLE = "Converte AI"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
OUTPUTS_URL_BASE = "/outputs"
os.makedirs(OUT_DIR, exist_ok=True)
VALIDATION_STL_PLACEHOLDER = os.path.join(OUT_DIR, "__placeholder__.stl")

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # para deploy


@server.route(f"{OUTPUTS_URL_BASE}/<path:filename>")
def serve_generated_outputs(filename):
    # Permite que o Dash sirva os arquivos STL gerados para o viewer
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

# Armazena caminho do último STL gerado
LAST_STL_PATH = None

# ---------------- Layout ----------------
main_layout = html.Main(
    className="frame",
    children=[
        html.Div(
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
                                html.Div([
                                    html.Label("Nome completo", className="field-label"),
                                    dcc.Input(id="customer-name", type="text", placeholder="Seu nome", className="field-input", maxLength=120),
                                ], className="field-block"),
                                html.Div([
                                    html.Label("E-mail", className="field-label"),
                                    dcc.Input(id="customer-email", type="email", placeholder="voce@email.com", className="field-input", maxLength=120),
                                ], className="field-block"),
                                html.Div([
                                    html.Label("Telefone/WhatsApp", className="field-label"),
                                    dcc.Input(id="customer-phone", type="text", placeholder="(11) 99999-0000", className="field-input", maxLength=20),
                                ], className="field-block"),
                                html.Div([
                                    html.Label("CPF/CNPJ", className="field-label"),
                                    dcc.Input(id="customer-doc", type="text", placeholder="Somente números", className="field-input", maxLength=20),
                                ], className="field-block"),
                                html.Div([
                                    html.Label("Observações", className="field-label"),
                                    dcc.Textarea(id="customer-notes", placeholder="Preferências, endereço, etc.", className="field-textarea", maxLength=500),
                                ], className="field-block wide"),
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
        ),
        html.Header(
            className="topbar",
            children=[
                html.Div(APP_TITLE, id="brand", className="brand"),
                html.Button(html.Div(className="hex"), id="btn-profile", className="hex-btn", title="Cadastro do cliente"),
            ],
        ),
        html.Section(
            className="content",
            children=[
                # ...existing code...
                dcc.Upload(
                    id="uploader",
                    accept="image/*",
                    multiple=False,
                    disabled=False,
                    className="dropzone",
                    children=html.Div(
                        className="drop-inner",
                        children=[
                            html.Div(className="upld", children=html.Span("⤴", className="upld-ico")),
                            html.Div("Solte a imagem aqui", className="drop-title"),
                            html.Div("ou clique para selecionar um arquivo", className="hint"),
                        ],
                    ),
                ),
                html.Div(
                    id="preview",
                    className="preview",
                    children=[
                        html.Div(
                            className="thumb",
                            children=[
                                html.Img(id="preview-img", src="", className="thumb-img", alt="preview"),
                                html.Button("×", id="remove-img", className="thumb-x", title="Remover imagem"),
                            ],
                        )
                    ],
                    style={"display": "none"},
                ),
                html.Div(
                    className="preproc-opts",
                    children=[
                        html.Label("Remover fundo?"),
                        dcc.Checklist(
                            id="do-remove-bg",
                            options=[{"label": "Sim", "value": "yes"}],
                            value=["yes"],
                            inline=True,
                        ),
                        html.Label("Foreground ratio (0.5 a 1.0):"),
                        dcc.Slider(
                            id="foreground-ratio",
                            min=0.5,
                            max=1.0,
                            step=0.05,
                            value=0.85,
                            marks={0.5: "0.5", 0.7: "0.7", 0.85: "0.85", 1.0: "1.0"},
                        ),
                    ],
                ),
                html.Div(
                    className="divider",
                    children=[html.Div(className="line"), html.Span("Ou"), html.Div(className="line")],
                ),
                html.Div("Insira sua descrição", className="label"),
                dcc.Textarea(
                    id="descricao",
                    className="textarea",
                    placeholder="Digite até 5000 caracteres...",
                    maxLength=5000,
                    disabled=False,
                    value="",
                ),
                html.Div(
                    className="meta",
                    children=[
                        html.Span("Nenhum arquivo selecionado", id="file-meta"),
                        html.Span([html.Span("0", id="count"), "/5000"]),
                    ],
                ),
                html.Div(
                    className="actions",
                    children=[
                        dcc.Loading(
                            id="loading-converter",
                            type="default",
                            children=html.Div(
                                id="conversion-spinner-target",
                                children=[
                                    html.Button("Converter", id="btn-converter", className="btn"),
                                    dcc.Download(id="download-stl"),
                                ],
                            ),
                        ),
                        html.Button("Limpar", id="btn-limpar", className="btn ghost"),
                    ],
                ),
                html.Div(id="main-loading"),
                dcc.Store(id="store-img", data=""),
                dcc.Store(id="store-customer", data={}),
            ],
        ),
    ],
)
# Callback para mostrar spinner futurista durante conversão
from dash.dependencies import Output as DashOutput, Input as DashInput

@app.callback(
    DashOutput("main-loading", "children"),
    [DashInput("btn-converter", "n_clicks")],
    prevent_initial_call=True,
)
def show_main_loading(n):
    if n:
        return html.Div([
            html.Div(className="futuristic-spinner"),
            html.Div("Convertendo imagem para modelo 3D...", style={"marginTop": "12px", "fontSize": "1.1rem", "color": "#7c4dff"})
        ], className="main-spinner")
    return ""


@app.callback(
    Output("customer-modal", "style"),
    Input("btn-profile", "n_clicks"),
    Input("close-customer-modal", "n_clicks"),
    Input("cancel-customer-modal", "n_clicks"),
    Input("customer-modal-backdrop", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_customer_modal(open_clicks, close_clicks, cancel_clicks, backdrop_clicks):
    trigger = ctx.triggered_id
    if trigger == "btn-profile":
        return {"display": "flex"}
    return {"display": "none"}


@app.callback(
    Output("customer-feedback", "children"),
    Output("store-customer", "data"),
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

    data = {
        "name": name,
        "email": email,
        "phone": phone_raw,
        "document": doc_raw,
        "notes": notes,
    }
    return html.Div("Cadastro salvo com sucesso. Você já pode avançar para o carrinho e pagamentos.", className="alert alert-success"), data

def stl_viewer_layout(stl_path):
    # Adiciona o novo CSS da visualização
    # Caminho relativo para o servidor Dash
    stl_url = f"{OUTPUTS_URL_BASE}/{os.path.basename(stl_path)}"
    loading = not os.path.exists(stl_path)
    return html.Main([
        html.Link(rel="stylesheet", href="/assets/style_viewer.css"),
        html.Header([
            html.Div(APP_TITLE, className="viewer-brand"),
            dcc.Link("Voltar", href="/", className="viewer-btn", id="btn-voltar", refresh=False),
        ], className="viewer-topbar"),
        html.Section([
            html.H3("Visualização 3D do modelo gerado", style={"marginBottom": "18px"}),
            (
                html.Div([
                    html.Div(className="futuristic-spinner"),
                    html.Div("Convertendo imagem para modelo 3D...", style={"marginTop": "18px", "fontSize": "1.2rem", "color": "#7c4dff"})
                ], className="viewer-spinner viewer-3d")
            ) if loading else dcc.Loading(
                id="loading-viewer",
                type="circle",
                children=[
                    html.Div([
                        dash_vtk.View([
                            dash_vtk.GeometryRepresentation([
                                dash_vtk.Reader(vtkClass="vtkSTLReader", url=stl_url)
                            ])
                        ], style={"height": "600px", "width": "100%"}),
                    ], className="viewer-3d")
                ],
                fullscreen=False,
            ),
            html.Div(f"Arquivo: {os.path.basename(stl_path)}", className="viewer-file"),
            html.Div([
                html.Button("Download STL", id="btn-download-viewer", className="viewer-btn", n_clicks=0),
                dcc.Download(id="download-stl-viewer"),
            ], className="viewer-download"),
        ], className="viewer-content"),
    ], className="viewer-frame")

app.validation_layout = html.Div([
    dcc.Location(id="url"),
    html.Div(id="_pages"),
    main_layout,
    stl_viewer_layout(VALIDATION_STL_PLACEHOLDER),
])

# ---------------- Helpers ----------------
def parse_upload(contents):
    """'data:image/png;base64,....' -> PIL.Image"""
    header, b64data = contents.split(",", 1)
    binary = base64.b64decode(b64data)
    img = Image.open(io.BytesIO(binary)).convert("RGB")
    return img


# --- TripoSR OBJ generation ---
def image_to_obj_triposr(pil_img, out_path_obj, do_remove_background=True, foreground_ratio=0.85):
    if preprocess is None or generate is None:
        raise RuntimeError("TripoSR não está disponível. Verifique o import.")
    # Preprocess image (params: do_remove_background, foreground_ratio)
    pre = preprocess(pil_img, do_remove_background=do_remove_background, foreground_ratio=foreground_ratio)
    # Sempre usar resolução máxima (320)
    obj_path, *_ = generate(pre, mc_resolution=320, formats=["obj"])
    # Move/copy OBJ to out_path_obj
    if obj_path != out_path_obj:
        import shutil
        shutil.copyfile(obj_path, out_path_obj)
    return out_path_obj

# --- Converter OBJ para STL (opcional) ---
def obj_to_stl(obj_path, stl_path):
    mesh = trimesh.load(obj_path)
    mesh.export(stl_path)
    return stl_path

def text_to_stl_mock(text, out_path):
    """Troque por Shap-E/Point-E."""
    r = min(2.0, 0.5 + len(text.strip()) / 1000.0)
    mesh = trimesh.creation.icosphere(radius=r, subdivisions=3)
    mesh.export(out_path)
    return out_path

# ---------------- Callback ÚNICO de UI (evita duplicidades) ----------------
@app.callback(
    Output("store-img", "data"),
    Output("uploader", "contents"),
    Output("uploader", "disabled"),
    Output("descricao", "value"),
    Output("descricao", "disabled"),
    Output("file-meta", "children"),
    Output("preview", "style"),
    Output("preview-img", "src"),
    Output("count", "children"),
    Input("uploader", "contents"),      # seleção de imagem
    Input("descricao", "value"),        # digitação de texto
    Input("remove-img", "n_clicks"),    # botão X do preview
    Input("btn-limpar", "n_clicks"),    # limpar geral
    State("store-img", "data"),
    prevent_initial_call=False,
)
def ui_state(upl_contents, texto, remove_clicks, clear_clicks, img_store):
    """
    Regras:
    - imagem selecionada -> mostra preview, desabilita texto, limpa texto
    - texto digitado (len>0) -> remove imagem, desabilita uploader
    - remover (X) -> remove imagem e libera texto
    - limpar -> limpa tudo
    - prioridade imagem (se por acaso houver ambos)
    """
    trigger = ctx.triggered_id  # quem disparou
    texto = (texto or "")

    # valores padrão atuais
    store = img_store or ""
    uploader_contents = no_update
    uploader_disabled = False
    desc_val = texto
    desc_disabled = False
    file_meta = "Nenhum arquivo selecionado"
    preview_style = {"display": "none"}
    preview_src = ""
    count = len(texto)

    # estado existente: se há imagem armazenada, aplica prioridade imagem
    if store:
        preview_style = {"display": "block"}
        preview_src = store
        desc_disabled = True
        desc_val = ""  # mantém textarea limpa quando há imagem
        file_meta = "1 arquivo selecionado"

    # --- eventos ---
    if trigger == "btn-limpar":
        # zera tudo
        return "", None, False, "", False, "Nenhum arquivo selecionado", {"display":"none"}, "", 0

    if trigger == "remove-img":
        # remove a imagem e libera texto
        return "", None, False, desc_val, False, "Nenhum arquivo selecionado", {"display":"none"}, "", len(desc_val)

    if trigger == "uploader":
        # nova imagem escolhida
        if upl_contents:
            size_kb = int(len(upl_contents) * 3 / 4 / 1024)
            file_meta = f"1 arquivo • ~{size_kb} KB"
            return upl_contents, upl_contents, False, "", True, file_meta, {"display":"block"}, upl_contents, 0

    # trigger == "descricao" (ou inicial)
    if len(texto) > 0 and not store:
        # texto em uso -> desabilita upload, esconde preview
        uploader_disabled = True
        file_meta = "Nenhum arquivo selecionado"
        return "", None, uploader_disabled, texto, False, file_meta, {"display":"none"}, "", len(texto)

    # caso inicial ou sem mudanças relevantes mantém estado atual
    return store, uploader_contents, desc_disabled, desc_val, desc_disabled, file_meta, preview_style, preview_src, count

# ---------------- Converter ----------------

# Callback para conversão e redirecionamento
from dash.dependencies import Output as DashOutput, Input as DashInput, State as DashState


# Callback para conversão e redirecionamento (sem download automático)
@app.callback(
    [
        DashOutput("url", "pathname"),
        DashOutput("conversion-spinner-target", "children"),
    ],
    [DashInput("btn-converter", "n_clicks")],
    [DashState("store-img", "data"), DashState("descricao", "value"), DashState("do-remove-bg", "value"), DashState("foreground-ratio", "value")],
    prevent_initial_call=True,
)
def run_convert(n, b64img, texto, do_remove_bg_val, fg_ratio):
    global LAST_STL_PATH
    texto = (texto or "").strip()
    if not b64img and not texto:
        return no_update, no_update
    out_name = f"{uuid.uuid4().hex[:8]}"
    obj_path = os.path.join(OUT_DIR, out_name + ".obj")
    stl_path = os.path.join(OUT_DIR, out_name + ".stl")
    do_remove_bg = bool(do_remove_bg_val and "yes" in do_remove_bg_val)
    fg_ratio = fg_ratio if fg_ratio is not None else 0.85
    if b64img:
        pil = parse_upload(b64img)
        image_to_obj_triposr(pil, obj_path, do_remove_background=do_remove_bg, foreground_ratio=fg_ratio)
        obj_to_stl(obj_path, stl_path)
        LAST_STL_PATH = stl_path
        return "/visualizar", ""
    else:
        text_to_stl_mock(texto, stl_path)
        LAST_STL_PATH = stl_path
        return "/visualizar", ""


# Callback para renderizar páginas
@app.callback(
    DashOutput("_pages", "children"),
    [DashInput("url", "pathname")],
)
def display_page(pathname):
    if pathname == "/visualizar" and LAST_STL_PATH:
        return stl_viewer_layout(LAST_STL_PATH)
    return main_layout

# Callback para download manual na visualização
@app.callback(
    DashOutput("download-stl-viewer", "data"),
    [DashInput("btn-download-viewer", "n_clicks")],
    prevent_initial_call=True,
)
def download_stl_viewer(n):
    if LAST_STL_PATH:
        return dcc.send_file(LAST_STL_PATH)
    return no_update

# Adiciona container para páginas
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div(id="_pages")
])

if __name__ == "__main__":
    app.run(host="localhost", port=8050, debug=True)
