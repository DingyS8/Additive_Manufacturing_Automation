import io, base64, uuid
from PIL import Image
from dash import html, dcc, Input, Output, State, no_update, ctx
from ..services.validation import is_allowed_image, is_allowed_model, check_size
from ..services.storage import save_base64_image, OUT_DIR
from ..services.generation import text_to_png, triposr_image_to_obj, obj_to_stl
from ..services.slicer import slice_model
from ..services.quote import estimate_from_gcode
from ..services.cart import add_item
from ..services.db import get_db
from ..services.models import file_doc
from ..services import generation as gen
from ..pages.viewer import set_last_stl

# TripoSR import (ajuste o path se necessário)
import sys, os
TRIPOSR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), r'C:\Users\vinic\Desktop\GitHub\TripoSR'))
if TRIPOSR_PATH not in sys.path: sys.path.insert(0, TRIPOSR_PATH)
try:
    from gradio_app import preprocess, generate
except ImportError:
    preprocess = None
    generate = None

def _render_convert_button():
    return html.Button(
        [
            html.Span("Converter p/ 3D", className="btn-label"),
            html.Span(className="btn-loader", **{"aria-hidden": "true"}),
        ],
        id="btn-3d",
        className="btn btn-with-loader",
    )

def layout():
    return html.Main(className="frame", children=[
        html.Header(className="topbar", children=[
            html.Div("Converte AI", id="brand", className="brand"),
            dcc.Link("Conta", href="/conta", className="btn ghost")
        ]),
        html.Section(className="content", children=[
            dcc.Upload(id="uploader", accept="image/*,.obj,.stl", multiple=False, className="dropzone",
                       children=html.Div(className="drop-inner", children=[
                           html.Div(className="upld", children=html.Span("⤴", className="upld-ico")),
                           html.Div("Solte a imagem/OBJ/STL aqui", className="drop-title"),
                           html.Div("ou clique para selecionar um arquivo (≤10MB)", className="hint"),
                       ])),
            html.Div(id="file-feedback", className="customer-feedback"),
            html.Div("Ou gere PNG a partir de texto (1–3000 caracteres)", className="label"),
            dcc.Textarea(id="texto", className="textarea", maxLength=3000, placeholder="Digite aqui..."),
            html.Div(className="actions", children=[
                html.Button("Gerar PNG", id="btn-png", className="btn"),
                html.Div(
                    id="btn-3d-wrapper",
                    children=_render_convert_button(),
                ),
                html.Button("Fatiar (G-code)", id="btn-slice", className="btn"),
                html.Button("Adicionar ao carrinho", id="btn-add-cart", className="btn ghost"),
                dcc.Download(id="download-png"),
            ]),
            dcc.Store(id="store-upload"),   # base64 do upload
            dcc.Store(id="store-stl"),
            dcc.Store(id="store-gcode"),
            dcc.Location(id="redirect-viewer", refresh=True),
        ])
    ])

def register_callbacks(app):
    @app.callback(
        Output("store-stl","data"),
        Output("redirect-viewer","pathname"),
        Output("btn-3d-wrapper","children"),
        Input("btn-3d","n_clicks"),
        State("store-upload","data"),
        prevent_initial_call=True
    )
    def gen_stl(n, data_url):
        if not data_url:
            return no_update, no_update, _render_convert_button()
        header, b64 = data_url.split(",",1)
        mime = header.split(":")[1].split(";")[0]
        binary = base64.b64decode(b64)
        ext = mime.split("/")[-1]

        if ext in ("png","jpeg","jpg"):
            pil = Image.open(io.BytesIO(binary)).convert("RGB")
            obj_path = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.obj")
            stl_path = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.stl")
            if preprocess and generate:
                try:
                    gen.triposr_image_to_obj(preprocess, generate, pil, obj_path)
                    gen.obj_to_stl(obj_path, stl_path)
                    set_last_stl(stl_path)
                    return stl_path, "/visualizar", _render_convert_button()
                except Exception as e:
                    return f"Erro na conversão IA: {e}", no_update, _render_convert_button()
            else:
                return "IA indisponível", no_update, _render_convert_button()
        elif ext in ("obj","stl"):
            temp_path = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.{ext}")
            with open(temp_path,"wb") as f: f.write(binary)
            if ext == "obj":
                stl_path = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.stl")
                gen.obj_to_stl(temp_path, stl_path)
            else:
                stl_path = temp_path
            set_last_stl(stl_path)
            return stl_path, "/visualizar", _render_convert_button()
        return no_update, no_update, _render_convert_button()
    from dash import callback_context

    @app.callback(
        Output("file-feedback","children"),
        Output("store-upload","data"),
        Input("uploader","contents"),
        State("uploader","filename"),
        Input("btn-add-cart","n_clicks"),
        State("store-gcode","data"),
        State("store-stl","data"),
        prevent_initial_call=True
    )
    def unified_feedback(contents, filename, n_add_cart, gcode_path, stl_path):
        triggered = callback_context.triggered[0]["prop_id"] if callback_context.triggered else None
        # Upload
        if triggered and triggered.startswith("uploader"):
            if not contents or not filename:
                return no_update, no_update
            header, b64 = contents.split(",",1)
            size_bytes = int(len(b64) * 3 / 4)
            if not check_size(size_bytes):
                return "Arquivo excede 10MB.", no_update
            ext = filename.split(".")[-1].lower()
            if not (is_allowed_image(filename) or is_allowed_model(filename)):
                return "Extensão não suportada.", no_update
            return f"Arquivo {filename} recebido.", contents
        # Adicionar ao carrinho
        elif triggered and triggered.startswith("btn-add-cart"):
            user_id = "demo-user"
            if gcode_path:
                quote = estimate_from_gcode(gcode_path)
                item = {"id": str(uuid.uuid4()), "type":"gcode", "path": gcode_path, "quote": quote}
            elif stl_path:
                item = {"id": str(uuid.uuid4()), "type":"stl", "path": stl_path}
            else:
                return "Nada para adicionar.", no_update
            add_item(user_id, item)
            return "Adicionado ao carrinho.", no_update
        return no_update, no_update

    # ...existing code for other callbacks (gen_png, gen_stl, do_slice)...
