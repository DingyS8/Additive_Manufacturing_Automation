import os, io, base64, uuid
from PIL import Image
import trimesh

from dash import Dash, html, dcc, Input, Output, State, no_update, ctx

APP_TITLE = "Converte AI"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # para deploy

# ---------------- Layout ----------------
app.layout = html.Main(
    className="frame",
    children=[
        html.Header(
            className="topbar",
            children=[
                html.Div(APP_TITLE, id="brand", className="brand"),
                html.Button(html.Div(className="hex"), className="hex-btn", title="Menu/Perfil"),
            ],
        ),
        html.Section(
            className="content",
            children=[
                # Upload (apenas 1 imagem)
                dcc.Upload(
                    id="uploader",
                    accept="image/*",
                    multiple=False,
                    disabled=False,  # será desabilitado quando texto estiver preenchido
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

                # Pré-visualização fixa (imagem + botão X). Só mudamos src/visibilidade.
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

                # Divider
                html.Div(
                    className="divider",
                    children=[html.Div(className="line"), html.Span("Ou"), html.Div(className="line")],
                ),

                # Texto
                html.Div("Insira sua descrição", className="label"),
                dcc.Textarea(
                    id="descricao",
                    className="textarea",
                    placeholder="Digite até 5000 caracteres...",
                    maxLength=5000,
                    disabled=False,  # será desabilitado quando houver imagem
                    value="",
                ),
                html.Div(
                    className="meta",
                    children=[
                        html.Span("Nenhum arquivo selecionado", id="file-meta"),
                        html.Span([html.Span("0", id="count"), "/5000"]),
                    ],
                ),

                # Ações
                html.Div(
                    className="actions",
                    children=[
                        html.Button("Converter", id="btn-converter", className="btn"),
                        html.Button("Limpar", id="btn-limpar", className="btn ghost"),
                        dcc.Download(id="download-stl"),
                    ],
                ),

                # Armazenamento (imagem única em base64)
                dcc.Store(id="store-img", data=""),
            ],
        ),
    ],
)

# ---------------- Helpers ----------------
def parse_upload(contents):
    """'data:image/png;base64,....' -> PIL.Image"""
    header, b64data = contents.split(",", 1)
    binary = base64.b64decode(b64data)
    img = Image.open(io.BytesIO(binary)).convert("RGB")
    return img

def image_to_stl_mock(pil_img, out_path):
    """Troque por TripoSR."""
    mesh = trimesh.creation.box(extents=(1, 1, 1))
    mesh.export(out_path)
    return out_path

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
@app.callback(
    Output("download-stl", "data"),
    Input("btn-converter", "n_clicks"),
    State("store-img", "data"),
    State("descricao", "value"),
    prevent_initial_call=True,
)
def run_convert(n, b64img, texto):
    texto = (texto or "").strip()

    if not b64img and not texto:
        return no_update

    # prioridade = imagem
    out_name = f"{uuid.uuid4().hex[:8]}.stl"
    out_path = os.path.join(OUT_DIR, out_name)

    if b64img:
        pil = parse_upload(b64img)
        image_to_stl_mock(pil, out_path)
    else:
        text_to_stl_mock(texto, out_path)

    return dcc.send_file(out_path)

if __name__ == "__main__":
    app.run(host="localhost", port=8050, debug=True)
