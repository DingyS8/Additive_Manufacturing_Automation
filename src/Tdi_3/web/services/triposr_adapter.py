import os, sys, shutil
from PIL import Image

TRIPOSR_PATH = os.path.abspath(r"C:\Users\vinic\Desktop\GitHub\TripoSR")
if TRIPOSR_PATH not in sys.path:
    sys.path.insert(0, TRIPOSR_PATH)

try:
    from gradio_app import preprocess, generate
except ImportError:
    preprocess = None
    generate = None

def ensure_available():
    if preprocess is None or generate is None:
        raise RuntimeError("TripoSR não disponível. Verifique path/import.")

def image_to_obj(pil_img, out_path_obj, remove_bg=True, fg_ratio=0.85):
    ensure_available()
    pre = preprocess(pil_img, do_remove_background=remove_bg, foreground_ratio=fg_ratio)
    obj_path, *_ = generate(pre, mc_resolution=320, formats=["obj"])
    if obj_path != out_path_obj:
        shutil.copyfile(obj_path, out_path_obj)
    return out_path_obj
