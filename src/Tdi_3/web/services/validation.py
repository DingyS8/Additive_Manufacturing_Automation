ALLOWED_IMAGES = {"png","jpg","jpeg"}
ALLOWED_MODELS = {"obj","stl"}
MAX_BYTES = 10 * 1024 * 1024

def is_allowed_image(filename: str) -> bool:
    return filename.split(".")[-1].lower() in ALLOWED_IMAGES

def is_allowed_model(filename: str) -> bool:
    return filename.split(".")[-1].lower() in ALLOWED_MODELS

def check_size(len_bytes: int) -> bool:
    return len_bytes <= MAX_BYTES
