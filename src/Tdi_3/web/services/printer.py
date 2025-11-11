import os, requests
from dotenv import load_dotenv
load_dotenv()

API = os.getenv("PRINTER_API", "http://127.0.0.1:7125")
TOKEN = os.getenv("PRINTER_TOKEN", "")

def _headers():
    return {"X-Api-Key": TOKEN} if TOKEN else {}

def set_printer_params(bed=None, nozzle=None):
    # mock simples—substitua por chamadas reais do Moonraker/OctoPrint
    return {"ok": True, "bed": bed, "nozzle": nozzle}

def upload_gcode(printer_id, path):
    # mock: “envia” arquivo
    return {"ok": True, "file": os.path.basename(path)}

def start_print(printer_id, file_name):
    # mock: “inicia” job
    return {"ok": True, "job": file_name}
