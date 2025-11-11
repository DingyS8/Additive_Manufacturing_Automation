import os, base64, uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
OUTPUTS_URL_BASE = "/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def save_base64_image(data_url: str) -> str:
    header, b64 = data_url.split(",", 1)
    ext = header.split("/")[1].split(";")[0]  # png/jpg/jpeg
    path = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.{ext}")
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path

def save_bytes(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)

def url_for_output(path: str) -> str:
    return f"{OUTPUTS_URL_BASE}/{os.path.basename(path)}"
