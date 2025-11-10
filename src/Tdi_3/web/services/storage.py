import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
OUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
OUTPUTS_URL_BASE = "/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def out_path(name, ext):
    return os.path.join(OUT_DIR, f"{name}.{ext}")
